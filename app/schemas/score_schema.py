from __future__ import annotations
from pydantic import BaseModel, Field


class ProductExcelRow(BaseModel):
  """엑셀 파일의 각 행 데이터 검증 양식"""

  product_name: str = Field(..., description="상품명 (필수)", alias="상품명")
  category: str = Field(..., description="카테고리 (필수)", alias="카테고리")
  quarter: str = Field(..., description="계절/분기 (필수)", alias="분석 시즌")
  exposure: float = Field(..., description="노출수", alias="노출수")
  click: float = Field(..., description="클릭수", alias="클릭수")
  visit: float = Field(..., description="상품 상세 방문수", alias="상품 상세 방문수")
  wish: float = Field(..., description="찜 유저수", alias="찜 유저수")
  cart: float = Field(..., description="장바구니 유저수", alias="장바구니 유저수")
  order_cnt: float = Field(..., description="상품주문수", alias="상품주문수")
  return_cnt: float = Field(..., description="반품건수", alias="반품건수")
  ad_cost: float = Field(..., description="광고과금액", alias="광고과금액")
  order_amount: float = Field(..., description="주문금액", alias="주문금액")
  item_price: float = Field(..., description="상품단가", alias="상품단가")
  analysis_start_time: str = Field(..., description="분석 시간", alias="분석 시작월")
  analysis_end_time: str = Field(..., description="분석 시간", alias="분석 종료월")

  class Config:
    populate_by_name = True