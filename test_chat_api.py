from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass


API_URL = "http://127.0.0.1:8000/chat"
TIMEOUT_SECONDS = 180


@dataclass(frozen=True)
class TestCase:
    name: str
    question: str
    required_terms: tuple[str, ...]
    forbidden_terms: tuple[str, ...] = (
        "질문에 직접 답변할 수 있는 근거 문서를 찾지 못했습니다",
        "$28",
        "미국 내 배송비",
        "국제택배비",
    )


TEST_CASES = (
    TestCase(
        name="판매자 정보 제공",
        question="플랫폼은 판매자 정보를 소비자에게 제공해야 하나요?",
        required_terms=("판매자", "청약", "제공"),
    ),
    TestCase(
        name="단순 변심 반품",
        question="단순 변심으로도 반품할 수 있나요?",
        required_terms=("7일 이내", "소비자가 부담"),
    ),
    TestCase(
        name="상품 불일치 반품 기한",
        question="상품 설명과 실제 상품이 다르면 언제까지 반품할 수 있나요?",
        required_terms=("3개월 이내", "30일 이내"),
    ),
    TestCase(
        name="품절 환불",
        question="품절이면 판매자는 언제 환불해야 하나요?",
        required_terms=("3영업일 이내", "환급"),
    ),
    TestCase(
        name="반품 비용 부담",
        question="반품 배송비는 누가 부담하나요?",
        required_terms=("소비자가 부담", "판매자가 반환 비용을 부담"),
    ),
    TestCase(
        name="반품 방해",
        question="쇼핑몰이 반품을 방해하면 어떻게 되나요?",
        required_terms=("방해해서는 안 됩니다",),
    ),
    TestCase(
        name="변형 - 마음이 바뀐 반품",
        question="마음이 바뀌었는데 받은 상품을 돌려보낼 수 있나요?",
        required_terms=("7일 이내", "소비자가 부담"),
    ),
    TestCase(
        name="변형 - 사진과 다른 상품",
        question="상품이 사진과 다른데 한 달이 지나도 반품할 수 있나요?",
        required_terms=("3개월 이내", "30일 이내"),
    ),
    TestCase(
        name="변형 - 반품 버튼 숨김",
        question="판매자가 반품 버튼을 숨기고 계속 거절하는데 문제가 없나요?",
        required_terms=("방해해서는 안 됩니다",),
    ),
    TestCase(
        name="변형 - 입점 판매자 정보",
        question="입점한 판매자의 이름이나 연락처를 구매 전에 확인할 수 있나요?",
        required_terms=("성명", "주소", "전화번호", "청약"),
    ),
    TestCase(
        name="변형 - 택배비 부담",
        question="마음에 들지 않아 반품하려는데 택배비는 누가 내야 하나요?",
        required_terms=("택배비는 소비자가 부담",),
    ),
    TestCase(
        name="변형 - 품절 결제금 환급",
        question="주문한 물건이 품절됐다고 하는데 결제한 돈은 언제 돌려받나요?",
        required_terms=("3영업일 이내", "환급"),
    ),
)


def request_chat(question: str) -> dict:
    payload = json.dumps(
        {"question": question},
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=TIMEOUT_SECONDS,
    ) as response:
        response_body = response.read().decode("utf-8")
        return json.loads(response_body)


def run_test(test_case: TestCase) -> tuple[bool, list[str]]:
    result = request_chat(test_case.question)
    answer = str(result.get("answer", ""))

    errors: list[str] = []

    if not answer.strip():
        errors.append("응답에 answer가 없습니다.")

    for term in test_case.required_terms:
        if term not in answer:
            errors.append(f"필수 문구 없음: {term}")

    for term in test_case.forbidden_terms:
        if term in answer:
            errors.append(f"금지 문구 포함: {term}")

    return not errors, errors


def main() -> int:
    passed = 0
    failed = 0

    print("=" * 72)
    print("FastAPI /chat 자동 회귀 테스트 시작")
    print(f"API URL: {API_URL}")
    print("=" * 72)

    for index, test_case in enumerate(TEST_CASES, start=1):
        print(f"\n[{index}/{len(TEST_CASES)}] {test_case.name}")
        print(f"질문: {test_case.question}")

        try:
            success, errors = run_test(test_case)
        except urllib.error.HTTPError as exc:
            success = False
            body = exc.read().decode("utf-8", errors="replace")
            errors = [
                f"HTTP 오류: {exc.code} {exc.reason}",
                f"응답: {body}",
            ]
        except urllib.error.URLError as exc:
            success = False
            errors = [
                "FastAPI 서버에 연결할 수 없습니다.",
                f"상세: {exc.reason}",
            ]
        except Exception as exc:
            success = False
            errors = [
                f"실행 오류: {type(exc).__name__}: {exc}",
            ]

        if success:
            passed += 1
            print("결과: PASS")
        else:
            failed += 1
            print("결과: FAIL")
            for error in errors:
                print(f"  - {error}")

    print("\n" + "=" * 72)
    print(f"전체: {len(TEST_CASES)}")
    print(f"성공: {passed}")
    print(f"실패: {failed}")
    print("=" * 72)

    if failed:
        print("API 테스트 실패 항목을 확인해주세요.")
        return 1

    print("FastAPI /chat 자동 테스트를 모두 통과했습니다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())