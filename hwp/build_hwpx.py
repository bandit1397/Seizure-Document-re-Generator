"""압수물 품명 오기 정정 서류를 한글(HWPX) 파일로 만든다.

사용법:
    pip install python-hwpx==6.8.0
    python hwp/build_hwpx.py

아래 CASE, ITEMS 값을 실제 사건에 맞게 고친 뒤 실행하면 hwp/ 폴더에 서류가 생성된다.
상황: 송치 시 함께 보낸 압수물 전체가 보완수사요구와 함께 경찰서로 반환된 경우.
"""
import warnings
from pathlib import Path

from hwpx.document import HwpxDocument

warnings.filterwarnings("ignore", category=DeprecationWarning)

OUT = Path(__file__).resolve().parent

# ── 사건 정보 (가상 예시) ────────────────────────────────────────────
CASE = dict(
    case_no="2026-000123",
    pro_case_no="2026형제○○○○○호",
    crime="절도",
    suspect="김○○",
    birth="19○○. ○. ○.",
    addr="○○시 ○○구 ○○로 ○○",
    crime_time="2026. 7. 3. 15:10경",
    seize_date="2026. 7. 3.",
    seize_time="2026. 7. 3. 15:20경",
    crime_place="서울 ○○구 ○○로 ○○ 소재 다이소 ○○점",
    seize_place="서울 ○○구 ○○로 ○○ 다이소 ○○점 출입구 앞",
    total="8종 10점",
    amount="18,000원",
    store="다이소 ○○점",
    manager="점장 이○○",
    send_date="2026. 7. 20.",
    request_date="2026. 10. 13.",
    return_date="2026. 10. 14.",
    check_time="2026. 10. 15. 14:00경",
    witness="경사 ○○○",
    reissue_date="2026. 10. 16.",
    write_date="2026. 10. 16.",
    pro_office="○○지방검찰청",
    prosecutor="검사 ○○○",
    station="○○경찰서",
    dept="형사과 강력○팀",
    dept_head="형사과장",
    officer="경위 홍길동",
    storage="당서 압수물 보관창고",
)

# 압수물 전체. before가 있으면 품명 오기 물품.
# check: 포장 표기로 확인 / 개봉 확인
ITEMS = [
    dict(no="1", name="주방세제", qty="1개", price="2,000원"),
    dict(no="2", name="쿨 팔토시(2개입)", before="장갑", qty="1개", code="품번 ○○○○○○", price="2,000원", check="포장 뒷면 표기 확인"),
    dict(no="3", name="볼펜세트", qty="1개", price="1,000원"),
    dict(no="4", name="C타입 이어폰 변환젠더", before="USB 충전케이블", qty="1개", code="품번 ○○○○○○", price="3,000원", check="참여인 입회 개봉 확인"),
    dict(no="5", name="수건", qty="2장", price="2,000원"),
    dict(no="6", name="발목 보호대", before="양말", qty="1개", code="품번 ○○○○○○", price="3,000원", check="포장 뒷면 표기 확인"),
    dict(no="7", name="AA 건전지(4개입)", qty="2팩", price="2,000원"),
    dict(no="8", name="물티슈", qty="1개", price="3,000원"),
]
WRONG = [i for i in ITEMS if i.get("before")]
OPENED = [i for i in WRONG if "개봉" in i.get("check", "")]
NOS = ", ".join(i["no"] for i in WRONG)
AFFECTED = "압수조서(압수경위란), 압수목록, 압수목록 교부서, 임의제출서, 압수물 총목록, 압수물 표지(꼬리표), 피의자신문조서"

TEXT_WIDTH = 48000  # A4, 좌우 여백 20mm 기준 본문 폭(HWP 단위)


class Builder:
    """HwpxDocument 위에 수사서류용 단락·표 헬퍼를 얹는다."""

    def __init__(self):
        self.doc = HwpxDocument.new()
        self.doc.set_page_setup(paper_size="A4", margin_left_mm=20, margin_right_mm=20,
                                margin_top_mm=20, margin_bottom_mm=15)
        self.started = False

    def _fmt(self, **kw):
        self.doc.set_paragraph_format(paragraph_index=len(self.doc.paragraphs) - 1, **kw)

    def p(self, text="", indent=0, align=None, bold=False, size=11, before=None, after=None):
        para = self.doc.add_paragraph("", include_run=False, inherit_style=False)
        para.add_run(text, bold=bold, size=size)
        kw = {}
        if align:
            kw["alignment"] = align
        if indent:
            kw["indent_left_mm"] = indent * 5
        if before is not None:
            kw["spacing_before_pt"] = before
        if after is not None:
            kw["spacing_after_pt"] = after
        if kw:
            self._fmt(**kw)

    def title(self, text, sub=None):
        para = self.doc.add_paragraph("", include_run=False, inherit_style=False)
        para.add_run(text, bold=True, size=20)
        kw = dict(alignment="center", spacing_after_pt=4 if sub else 14)
        if self.started:
            kw["page_break_before"] = True
        self._fmt(**kw)
        self.started = True
        if sub:
            self.p(sub, align="center", after=14)

    def table(self, rows, widths, header=True):
        t = self.doc.add_table(len(rows), len(rows[0]), width=TEXT_WIDTH)
        t.set_column_widths(widths)
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                t.set_cell_text(r, c, str(val), split_paragraphs="\n" in str(val))
                if header and r == 0:
                    t.set_cell_shading(r, c, "#E6E6E6")
        return t

    def sign(self, *lines):
        self.p("", after=6)
        for ln in lines:
            self.p(ln, align="right", after=4)

    def save(self, name):
        report = self.doc.validate()
        if report.issues:
            raise SystemExit(f"{name}: 검증 실패 {report.issues}")
        path = OUT / name
        self.doc.save_to_path(path)
        print("생성:", path.name)


C = CASE


# ── 서류 ────────────────────────────────────────────────────────────
def doc_report(b):
    n = len(WRONG)
    b.title("수 사 보 고")
    b.p(C["write_date"], align="right")
    b.p(f"수    신 : {C['station']}장")
    b.p(f"참    조 : {C['dept_head']}")
    b.p("제    목 : 압수물 품명 오기 확인 및 정정 보고(보완수사요구 이행)", after=8)
    b.p(f"  피의자 {C['suspect']}에 대한 {C['crime']} 사건({C['case_no']})에 관하여, {C['pro_office']} "
        f"{C['prosecutor']}의 {C['request_date']}자 보완수사요구(압수물 품명 불일치)에 따라 반환받은 "
        f"압수물 현품을 확인하였기에 다음과 같이 보고합니다.", after=6)

    b.p("1. 압수 및 송치 경위", bold=True)
    b.p(f"가. 피의자는 {C['crime_time']} {C['crime_place']}에서 진열된 생활용품 {C['total']}(시가 합계 "
        f"{C['amount']} 상당)을 절취하였다는 혐의로 {C['seize_time']} {C['seize_place']}에서 현행범인으로 "
        f"체포되었음.", indent=1)
    b.p(f"나. 체포 현장에서 피의자로부터 위 물품 {C['total']}을 임의제출받아 압수하고(형사소송법 제218조), "
        f"압수조서 및 압수목록을 작성하였으며, 임의제출자인 피의자에게 압수목록을 교부하였음.", indent=1)
    b.p(f"다. {C['send_date']} 위 사건을 송치하면서 압수물 {C['total']}을 함께 송부하였음.", indent=1, after=6)

    b.p("2. 보완수사요구 내용 및 압수물 반환", bold=True)
    b.p(f"가. 요구 내용 : 압수목록상 압수물의 수량({C['total']})은 일치하나, 일부 압수물의 품명이 실제 "
        f"물품과 일치하지 않으므로 이를 확인하여 보완할 것.", indent=1)
    b.p(f"나. 압수물 반환 : {C['return_date']} 송부하였던 압수물 {C['total']} 전부를 반환받아 압수목록과 "
        f"수량을 대조한 결과 이상이 없었으며, {C['storage']}에 보관하였음.", indent=1, after=6)

    b.p("3. 현품 확인 결과", bold=True)
    b.p(f"가. 확인 일시·장소 : {C['check_time']}, {C['storage']}", indent=1)
    b.p(f"나. 참여인 : {C['witness']}", indent=1)
    b.p("다. 확인 방법", indent=1)
    b.p("(1) 각 압수물에 부착된 압수물 표지(꼬리표)의 연번과 압수목록의 연번을 대조함.", indent=2)
    b.p("(2) 각 포장의 앞면과 뒷면에 표기된 상품명 및 상품코드(품번)를 확인함.", indent=2)
    if OPENED:
        nos = ", ".join(i["no"] for i in OPENED)
        b.p(f"(3) 포장 표기만으로 내용물을 특정하기 어려운 연번 {nos}번 물품은 참여인이 입회한 가운데 포장을 "
            f"개봉하여 내용물을 확인한 뒤 원래 포장에 다시 넣고 봉인지를 붙였음.", indent=2)
        b.p("(4) 위 확인 과정을 모두 촬영하였음(사진대지 첨부).", indent=2)
    else:
        b.p("(3) 위 확인 과정을 모두 촬영하였음(사진대지 첨부).", indent=2)
    b.p("라. 오기 원인", indent=1)
    b.p("압수 당시 압수물은 모두 판매용 포장이 개봉되지 않은 상태였으며, 피해품의 상품가치를 보전하기 "
        f"위하여 포장을 개봉하지 않고 포장의 그림과 형태만 보고 품명을 기재하였음. 이 과정에서 {n}건의 "
        "내용물을 잘못 판단하여 품명을 다르게 기재하였음.", indent=2)
    b.p("마. 확인 결과", indent=1)
    b.table([["연번", "기재 품명(정정 전)", "실제 품명(정정 후)", "수량", "상품코드", "확인 방법"]] +
            [[i["no"], i["before"], i["name"], i["qty"], i["code"], i["check"]] for i in WRONG],
            [8, 20, 24, 9, 17, 22])
    others = ", ".join(i["no"] for i in ITEMS if not i.get("before"))
    b.p(f"※ 그 밖의 압수물(연번 {others})은 압수목록의 품명·수량과 일치함.", indent=2, size=10)
    b.p("바. 동일성 판단", indent=1)
    b.p("압수물 표지의 연번, 수량, 포장 외관이 압수 당시와 같고, 압수 당시 사진과도 일치하므로, 이번 정정은 "
        "같은 물품의 품명 기재 오류를 바로잡는 것일 뿐이며 압수 대상이나 수량에는 변동이 없음.", indent=2)
    b.p("사. 피해액 영향", indent=1)
    b.p(f"피해업체 {C['store']} {C['manager']}에게 정정 후 품명의 상품코드와 판매가를 확인한 결과, "
        f"정정 전후 판매가가 같아 피해액 합계({C['amount']})는 변동 없음.", indent=2)
    b.p("아. 같은 품명이 기재된 서류", indent=1)
    b.p(f"{AFFECTED}에 같은 오기가 있으며, 별첨 대조표와 같이 정리하였음.", indent=2, after=6)

    b.p("4. 조치 사항", bold=True)
    b.p("가. 송치한 압수 관련 서류의 원본은 수정하거나 다시 작성하지 않고 그대로 두며, 본 수사보고와 "
        "별첨 대조표로 정정 내용을 명확히 함.", indent=1)
    b.p(f"나. 연번 {NOS} 압수물에는 기존 압수물 표지를 그대로 둔 채 정정 품명을 적은 보충 표지를 "
        "덧붙였음.", indent=1)
    b.p(f"다. {C['reissue_date']} 임의제출자인 피의자 {C['suspect']}에게 품명을 정정한 압수목록을 교부하고 "
        "수령 확인을 받았으며, 정정된 물품이 당시 제출한 물품과 같다는 임의제출자 확인서를 받았음.", indent=1)
    b.p(f"라. 품명을 정정한 압수물 총목록을 작성하여, 반환받은 압수물 {C['total']}을 보완수사 결과와 함께 "
        "다시 송부하고자 함.", indent=1)
    b.p("마. 피의자가 작성한 소유권포기서는 피해품에 관한 것이어서 그 포기 의사표시로 효력이 생기지 "
        "않으므로 다시 받지 않음.", indent=1, after=6)

    b.p("첨    부 : 1. 압수물 품명 정정 전·후 대조표 1부.")
    for k, t in enumerate(["사진대지", "압수목록 교부서(품명 정정) 사본", "임의제출자 확인서",
                           "피해품 확인서", "압수물 총목록(품명 정정)"], start=2):
        b.p(f"{k}. {t} 1부.", indent=2)
    b.p("끝.", align="right")
    b.sign(f"{C['station']} {C['dept']}", f"사법경찰관 {C['officer']}  (인)")


def doc_compare(b):
    b.title("압수물 품명 정정 전·후 대조표")
    b.p(f"사건번호 : {C['case_no']}      죄명 : {C['crime']}      피의자 : {C['suspect']}")
    b.p(f"최초 압수일시 : {C['seize_time']}      작성일 : {C['write_date']}", after=6)
    b.table([["연번", "정정 전", "정정 후", "수량", "상품코드", "단가"]] +
            [[i["no"], i["before"], i["name"], i["qty"], i["code"], i["price"]] for i in WRONG],
            [8, 20, 26, 9, 20, 13])
    b.p("", after=2)
    b.p(f"1. 같은 오기가 있는 서류 : {AFFECTED}")
    b.p("2. 정정 사유 : 미개봉 상품을 포장 외관만 보고 품명을 기재하여 생긴 오기")
    b.p("3. 확인 근거 : 반환받은 압수물 현품 확인(포장 표기, 필요시 개봉), 압수 당시 사진")
    b.p(f"4. 정정 범위 : 총 {C['total']} 중 연번 {NOS}의 품명에 한정함. 수량, 압수일시, 압수장소, "
        "그 밖의 물품은 변경하지 않음.")
    b.p("5. 비    고 : 본 대조표는 송치된 원본 서류를 대체하지 않음.")
    b.sign(f"작성자 사법경찰관 {C['officer']}  (인)")


def doc_photo(b):
    b.title("사 진 대 지", "(압수물 품명 정정 확인)")
    b.p(f"사건번호 : {C['case_no']}      촬영일시 : {C['check_time']}      장소 : {C['storage']}", after=6)
    marks = "①②③④⑤⑥⑦⑧⑨⑩"
    for k, i in enumerate(WRONG):
        m = marks[k]
        rows = [[f"사진 {m}-1  연번 {i['no']} 포장 앞면 (기재 품명: {i['before']})",
                 f"사진 {m}-2  연번 {i['no']} 포장 뒷면 상품명·품번 → {i['name']}"],
                ["\n\n\n\n(사진 부착)\n\n\n\n", "\n\n\n\n(사진 부착)\n\n\n\n"]]
        if "개봉" in i.get("check", ""):
            rows.append([f"사진 {m}-3  연번 {i['no']} 참여인 입회 개봉 후 내용물",
                         f"사진 {m}-4  연번 {i['no']} 재포장·봉인지 부착"])
            rows.append(["\n\n\n\n(사진 부착)\n\n\n\n", "\n\n\n\n(사진 부착)\n\n\n\n"])
        b.table(rows, [1, 1], header=False)
        b.p("", after=4)
    b.sign(f"촬영자 사법경찰관 {C['officer']}  (인)", f"참여인 {C['witness']}  (인)")


def doc_reissue(b):
    b.title("압 수 목 록 교 부 서", "(품명 정정)")
    b.p(f"사건번호 : {C['case_no']}          죄명 : {C['crime']}")
    b.p(f"피압수자(임의제출자) : {C['suspect']}")
    b.p(f"최초 압수일시 : {C['seize_time']}")
    b.p(f"최초 압수장소 : {C['seize_place']}", after=6)
    b.p(f"  귀하가 {C['seize_date']} 임의제출하여 압수한 물건 {C['total']} 중 아래 {len(WRONG)}건의 품명이 "
        "실제 물품과 다르게 기재되어 있었으므로, 이를 정정한 압수목록을 교부합니다.", after=4)
    b.table([["연번", "정정 전 품명", "정정 후 품명", "수량", "비고"]] +
            [[i["no"], i["before"], i["name"], i["qty"], "포장 미개봉 상태로 외관만 보고 오기" if k == 0 else "위와 같음"]
             for k, i in enumerate(WRONG)],
            [8, 22, 28, 9, 33])
    b.p("※ 위 물품 외 나머지 압수물의 품명과 수량은 최초 교부한 압수목록과 같습니다.", size=10, before=4)
    b.p("※ 이번 정정은 품명 기재를 바로잡는 것이며, 압수물을 추가하거나 바꾸는 것이 아닙니다.", size=10)
    b.p("※ 최초 교부한 압수목록 교부서는 그대로 유효하며, 본 서류는 이를 보충합니다.", size=10, after=10)
    b.p(C["reissue_date"], align="center", after=6)
    b.p(f"{C['station']} 사법경찰관 {C['officer']}  (인)", align="right", after=14)
    b.p("─────────────────  수 령 확 인  ─────────────────", align="center", after=6)
    b.p("본인은 위 품명 정정 압수목록을 교부받았습니다.")
    b.p(f"교부일시 : {C['reissue_date']}     :          교부장소 : {C['station']} {C['dept']}", after=6)
    b.p(f"수령인 : {C['suspect']}  (서명 또는 무인)", align="right")


def doc_submitter(b):
    b.title("임 의 제 출 자  확 인 서")
    b.p(f"성    명 : {C['suspect']} ({C['birth']}생)")
    b.p(f"주    거 : {C['addr']}", after=8)
    b.p(f"  본인은 {C['seize_time']} {C['seize_place']}에서 가방 안에 있던 물건 {C['total']}을 "
        "경찰관에게 임의제출하였습니다.", after=4)
    b.p("  오늘 경찰관으로부터, 당시 작성된 압수목록 중 아래 물건의 품명이 실제와 다르게 적혀 있었다는 "
        "설명을 듣고, 현품 사진을 확인하였습니다.", after=4)
    for i in WRONG:
        b.p(f"- 연번 {i['no']} : {i['before']} → {i['name']} {i['qty']}", indent=2)
    b.p("  위 물건은 당시 제가 제출한 물건과 같은 물건이며, 포장을 뜯지 않은 상태여서 안에 무엇이 "
        "들었는지 정확히 알지 못했습니다. 정정된 품명에 이의가 없습니다.", before=4, after=14)
    b.p(C["reissue_date"], align="center", after=10)
    b.sign(f"확 인 자 : {C['suspect']}  (서명 또는 무인)", f"확인 경찰관 : {C['station']} {C['officer']}  (인)")


def doc_victim(b):
    b.title("피 해 품  확 인 서")
    b.p(f"업 체 명 : {C['store']}")
    b.p(f"확 인 자 : {C['manager']}  (연락처 010-○○○○-○○○○)", after=8)
    b.p(f"  본인은 {C['seize_date']} 당 매장에서 도난당한 상품 중 아래 상품에 대하여, 경찰관이 제시한 "
        "현품 사진과 상품코드를 당사 상품정보로 조회하여 다음과 같이 확인합니다.", after=4)
    b.table([["연번", "경찰 기재 품명", "당사 상품명", "상품코드", "판매가", "수량"]] +
            [[i["no"], i["before"], i["name"], i["code"], i["price"], i["qty"]] for i in WRONG],
            [8, 20, 26, 20, 13, 9])
    b.p(f"  위 상품은 당일 도난당한 상품과 같으며, 피해품 전체 {C['total']}의 판매가 합계는 "
        f"{C['amount']}입니다.", before=4, after=14)
    b.p("2026.     .     .", align="center", after=10)
    b.sign(f"확 인 자 : {C['store']} {C['manager']}  (서명)", f"확인 경찰관 : {C['station']} {C['officer']}  (인)")


def doc_total(b):
    b.title("압 수 물  총 목 록", "(품명 정정)")
    b.p(f"사건번호 : {C['case_no']}      죄명 : {C['crime']}      피의자 : {C['suspect']}")
    b.p(f"압수일시 : {C['seize_time']}      작성일 : {C['write_date']}", after=6)
    b.table([["연번", "품명", "수량", "제출자", "소유자", "비고"]] +
            [[i["no"], i["name"], i["qty"], C["suspect"], C["store"],
              f"품명 정정(구: {i['before']})" if i.get("before") else ""] for i in ITEMS],
            [8, 28, 10, 13, 17, 24])
    b.p(f"합계 : {C['total']}", align="right", before=4)
    b.p(f"※ 본 목록은 {C['send_date']} 송치 시 첨부한 압수물 총목록 중 연번 {NOS}의 품명 오기를 정정하여 "
        "작성한 것으로, 원본을 대체하지 않음.", size=10, before=6)
    b.sign(f"작성자 사법경찰관 {C['officer']}  (인)")


def doc_notice(b):
    b.title(" ".join(C["station"]))
    b.p(f"수    신 : {C['pro_office']} {C['prosecutor']}")
    b.p("제    목 : 보완수사 결과 통보", after=8)
    b.p(f"1. 관련 : {C['pro_office']} {C['pro_case_no']}({C['request_date']}자 보완수사요구)")
    b.p(f"2. 피의자 {C['suspect']}에 대한 {C['crime']} 사건과 관련하여 요구하신 보완수사를 이행하였기에 "
        "그 결과를 다음과 같이 통보합니다.")
    b.p("가. 요구사항 : 압수목록상 일부 압수물의 품명 불일치 확인 및 보완", indent=1)
    b.p("나. 이행결과", indent=1)
    b.p(f"(1) {C['return_date']} 반환받은 압수물 {C['total']}의 현품을 {C['check_time']} 참여인 입회하에 "
        f"확인한 결과, 연번 {NOS}의 품명이 실제 물품과 다르게 기재된 사실을 확인함(미개봉 포장 외관에 "
        "따른 오기).", indent=2)
    for i in WRONG:
        b.p(f"- 연번 {i['no']} : {i['before']} → {i['name']} {i['qty']}", indent=3)
    b.p(f"(2) 압수물 표지, 포장 표기, 압수 당시 사진을 대조하여 동일한 물품임을 확인함. 압수 대상과 "
        f"수량은 변동이 없으며, 피해액({C['amount']})에도 변동이 없음.", indent=2)
    b.p(f"(3) 송치된 원본 서류는 그대로 두고, 임의제출자에게 품명을 정정한 압수목록을 다시 교부함"
        f"({C['reissue_date']}).", indent=2)
    b.p(f"(4) 압수물 {C['total']}을 품명 정정 압수물 총목록과 함께 다시 송부함.", indent=2, after=6)
    b.p("붙    임 : 1. 수사보고(압수물 품명 오기 확인 및 정정) 1부.")
    for k, t in enumerate(["압수물 품명 정정 전·후 대조표", "사진대지", "압수목록 교부서(품명 정정) 사본",
                           "임의제출자 확인서", "피해품 확인서", "압수물 총목록(품명 정정)"], start=2):
        b.p(f"{k}. {t} 1부.", indent=2)
    b.p(f"8. 압수물 {C['total']}.  끝.", indent=2)
    b.p("", after=14)
    b.p(f"{C['station']}장  (직인)", align="center", bold=True, size=15)


def doc_addsend(b):
    b.title("추  송  서")
    b.p(f"수    신 : {C['pro_office']} {C['prosecutor']}")
    b.p("제    목 : 압수물 품명 정정 관련 서류 추송", after=8)
    b.p(f"  {C['send_date']} 송치한 피의자 {C['suspect']}에 대한 {C['crime']} 사건({C['pro_case_no']})과 관련하여, "
        f"{C['return_date']} 반환받은 압수물의 현품을 확인한 결과 압수목록 연번 {NOS}의 품명 오기를 확인하고 "
        "정정한 서류를 다음과 같이 추가로 보냅니다.", after=4)
    for i in WRONG:
        b.p(f"- 연번 {i['no']} : {i['before']} → {i['name']} {i['qty']}", indent=2)
    b.p(f"  압수 대상, 수량, 피해액({C['amount']})에는 변동이 없으며, 이번 추송은 송치된 압수 관련 서류의 "
        "원본을 대체하지 않고 품명 오기의 경위와 정정 내용을 명확히 하기 위한 것입니다.", before=4, after=6)
    b.p("붙    임 : 1. 수사보고(압수물 품명 오기 확인 및 정정) 1부.")
    for k, t in enumerate(["압수물 품명 정정 전·후 대조표", "사진대지", "압수목록 교부서(품명 정정) 사본",
                           "임의제출자 확인서", "피해품 확인서", "압수물 총목록(품명 정정)"], start=2):
        b.p(f"{k}. {t} 1부.", indent=2)
    b.p(f"8. 압수물 {C['total']}.  끝.", indent=2)
    b.p("", after=14)
    b.p(f"{C['station']}장  (직인)", align="center", bold=True, size=15)


DOCS = [
    ("01_수사보고(압수물품명정정).hwpx", doc_report),
    ("02_압수물품명_정정전후_대조표.hwpx", doc_compare),
    ("03_사진대지.hwpx", doc_photo),
    ("04_압수목록교부서(품명정정).hwpx", doc_reissue),
    ("05_임의제출자_확인서.hwpx", doc_submitter),
    ("06_피해품_확인서.hwpx", doc_victim),
    ("07_압수물총목록(품명정정).hwpx", doc_total),
    ("08_보완수사결과_통보서.hwpx", doc_notice),
    ("09_추송서(08대신_택1).hwpx", doc_addsend),
]

if __name__ == "__main__":
    for name, fn in DOCS:
        b = Builder()
        fn(b)
        b.save(name)
    whole = Builder()
    for _, fn in DOCS[:-1]:
        fn(whole)
    whole.save("00_전체묶음(01-08).hwpx")
