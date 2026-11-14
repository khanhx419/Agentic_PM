import time
from llm import ModelError

# ==============================================================================
# HỆ THỐNG PROMPT CHO CÁC SPOKE AGENTS
# ==============================================================================

# Quy định chung bắt buộc cho LLM:
# - Không được bịa đặt kết quả kiểm thử (chỉ Python backend mới có quyền phán quyết PASS/FAIL)
# - Chỉ trả về JSON thuần túy, giải thích bằng tiếng Việt.
COMMON = (
    'The user is demonstrating a small real system. Do not fabricate a test result or say a checker passed. '
    'All checks run in separate trusted Python code. Explanations in Vietnamese, JSON keys as specified. '
)

PROMPTS = {
    # --------------------------------------------------------------------------
    # Prompt cho Planner Spoke:
    # Yêu cầu phân rã bài toán thành User Story nhỏ gọn cho hàm validate_email(email) -> bool
    # --------------------------------------------------------------------------
    'planner': COMMON + (
        'You are Story Planner. Break the request into ONE narrowly scoped story for a Python function '
        'validate_email(email) -> bool. Contract: trim surrounding whitespace, accept a simple address with '
        'exactly one @, nonempty local part, a domain containing a dot with nonempty labels, no embedded whitespace. '
        'Do not implement RFC-perfect email or network checks. Policy: no hardcoded secrets, no I/O, only imports re '
        'and os, only os.getenv for configuration. Return {"story":{"title":"...","acceptance":["..."],"scope":"..."}}. '
        'State unsupported requests in scope, do not silently broaden the task.'
    ),

    # --------------------------------------------------------------------------
    # Prompt cho Developer Spoke:
    # Hướng dẫn viết hàm Python đúng tiêu chuẩn, không dùng vòng lặp phức tạp hoặc hàm bị cấm
    # --------------------------------------------------------------------------
    'developer': COMMON + (
        'You are Developer. Implement exactly one Python function validate_email(email) -> bool, following story and '
        'trusted contract. Allowed subset: imports re and os (or from os import getenv), module constants, def with one '
        'argument, local assignments, if/elif/else, return, boolean/comparison operations, string strip/lower/split/count/'
        'startswith/endswith, len, bool, re.fullmatch/match/search. No loops, helper functions, decorators, comprehensions, '
        'exception blocks, eval, exec, filesystem, network or environment printing. Use '
        're.fullmatch(r"[^@\\s]+@[^@.\\s]+(?:\\.[^@.\\s]+)+", email.strip()) is not None for a straightforward supported solution. '
        'If secret configuration is needed, use os.getenv("SECRET_KEY") without literal fallback. Do not add secret configuration '
        'when unnecessary. Return {"code":"Python source only, no markdown","summary":"..."}. If feedback is present, fix the '
        'actual code based on failing tests and AST findings, preserve supported interface. Never return a made-up PASS.'
    ),
}


# ==============================================================================
# QUẢN LÝ DỮ LIỆU VÀ SỰ KIỆN CỦA PHIÊN (SESSION PIPELINE)
# ==============================================================================

def initial(kind, description, initial_code=''):
    """
    Khởi tạo dictionary trạng thái ban đầu của một phiên làm việc (Session State).
    Mỗi lần người dùng bấm nút trên Web, trạng thái này sẽ được chuyển đúng một bước.
    """
    if kind != 'hub':
        raise ValueError('Bản demo này chỉ hỗ trợ Hub-and-Spoke.')
    if not isinstance(description, str) or not 20 <= len(description) <= 10000:
        raise ValueError('Yêu cầu cần từ 20 đến 10.000 ký tự.')
    if not isinstance(initial_code, str) or len(initial_code) > 12000:
        raise ValueError('Mã đầu vào quá dài.')

    return {
        'kind': kind,
        'description': description,
        'initial_code': initial_code,
        'phase': 'ready',       # Giai đoạn hiện tại (ready -> planned -> coded -> review/blocked -> accepted)
        'status': 'ready',      # Trạng thái tổng quát của phiên
        'story': None,          # User story do Planner sinh ra
        'code': '',             # Mã nguồn Python hiện tại
        'revision': 0,          # Số phiên bản mã (r1, r2, r3)
        'qa': None,             # Kết quả kiểm thử từ QA Spoke
        'governance': None,     # Kết quả kiểm tra bảo mật từ Governance Spoke
        'repairs': 0,           # Số lần đã tự động sửa (tối đa 3 lần)
        'events': [],           # Dòng thời gian các sự kiện giữa các Agent
        'calls': [],            # Thống kê số lần và thời gian gọi LLM
        'last_error': None,     # Lỗi gần nhất (nếu có)
        'created_at': time.time(),
        'version': 0            # Số hiệu phiên bản trạng thái để chống xung đột đồng thời (optimistic lock)
    }


def event(s, actor, message):
    """Ghi nhận một sự kiện vào lịch sử (ví dụ: 'Planner → Coordinator: Đã tạo story')"""
    s['events'].append({'actor': actor, 'message': message, 'time': time.time()})


def call(s, model, role, payload):
    """
    Gọi Spoke Agent thông qua Model LLM.
    Mỗi role dùng một instruction/prompt riêng nhưng dùng chung LLM Gateway.
    """
    data, meta = model.call(role, PROMPTS[role], payload)
    s['calls'].append(meta)
    if not isinstance(data, dict):
        raise ModelError('Kết quả agent không phải JSON object.')
    return data


def get_code(data):
    """Trích xuất và kiểm tra tính hợp lệ của mã Python từ phản hồi JSON của Developer Spoke"""
    code = data.get('code')
    if not isinstance(code, str) or not 1 <= len(code) <= 12000:
        raise ModelError('Developer không trả mã Python hợp lệ trong trường code.')
    if code.strip().startswith('```'):
        raise ModelError('Developer trả markdown thay vì mã nguồn thuần. Thử lại bước này.')
    return code


def advance(state, model, confirmed=False):
    """
    Hàm cầu nối: Chuyển yêu cầu từ API Server vào Engine đồ thị LangGraph (workflow.run_step).
    """
    from workflow import run_step
    return run_step(state, model, confirmed)
