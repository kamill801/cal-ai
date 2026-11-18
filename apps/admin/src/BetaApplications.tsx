import { ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import type { AdminBetaApplications } from "./types";

export const BETA_PAGE_SIZE = 50;

type Props = {
  data: AdminBetaApplications | null;
  offset: number;
  loading: boolean;
  disabled: boolean;
  error: string | null;
  onRefresh: () => void;
  onPage: (offset: number) => void;
};

export function BetaApplications({ data, offset, loading, disabled, error, onRefresh, onPage }: Props) {
  const total = data?.total ?? 0;
  const page = Math.floor(offset / BETA_PAGE_SIZE) + 1;
  const pages = Math.max(1, Math.ceil(total / BETA_PAGE_SIZE));
  return (
    <section className="beta-section" aria-labelledby="beta-applications-title" aria-busy={loading}>
      <div className="section-heading beta-heading">
        <div>
          <h2 id="beta-applications-title">베타 신청자</h2>
          <p>보관 중인 전체 신청자 <strong>{data ? total.toLocaleString("ko-KR") : "-"}명</strong></p>
          <p>신청 후 30일 보관 · 중복 이메일·만료된 신청 제외</p>
        </div>
        <button className="icon-button" type="button" title="베타 신청자 새로고침" aria-label="베타 신청자 새로고침"
          disabled={disabled || loading} onClick={onRefresh}>
          <RefreshCw size={16} className={loading ? "spin" : undefined} />
        </button>
      </div>
      <div className="beta-status" role="status">
        {disabled ? "관리자 접근 권한을 다시 확인해 주세요." : loading ? "신청자 목록을 불러오는 중이에요." :
          data ? `조회 시각 ${seoulTimestamp(data.generated_at)} (Asia/Seoul)` : null}
      </div>
      {error && !disabled ? <div className="beta-error" role="alert">
        <p>{error}</p>
        <button className="primary-button" type="button" disabled={loading} onClick={onRefresh}>
          <RefreshCw size={14} />다시 시도
        </button>
      </div> : null}
      {data && !disabled ? data.applications.length ? (
        <div className="table-wrap">
          <table className="beta-table">
            <thead><tr><th scope="col">이메일</th><th scope="col">신청 시각 (Asia/Seoul)</th></tr></thead>
            <tbody>{data.applications.map((item) => <tr key={item.id}>
              <td className="beta-email">{item.email}</td>
              <td><time dateTime={item.created_at}>{seoulTimestamp(item.created_at)}</time></td>
            </tr>)}</tbody>
          </table>
        </div>
      ) : <p className="empty-state">보관 중인 베타 신청자가 없어요.</p> : null}
      <nav className="beta-pagination" aria-label="베타 신청자 페이지">
        <button className="icon-button" type="button" title="이전 페이지" aria-label="이전 페이지"
          disabled={disabled || loading || offset === 0} onClick={() => onPage(Math.max(0, offset - BETA_PAGE_SIZE))}>
          <ChevronLeft size={16} />
        </button>
        <span aria-live="polite">{data && !disabled ? `${page} / ${pages}페이지 · ${total ? offset + 1 : 0}-${Math.min(offset + data.applications.length, total)} / ${total.toLocaleString("ko-KR")}명` : "페이지 정보 확인 중"}</span>
        <button className="icon-button" type="button" title="다음 페이지" aria-label="다음 페이지"
          disabled={disabled || loading || !data || offset + BETA_PAGE_SIZE >= total || offset + BETA_PAGE_SIZE > 100_000}
          onClick={() => onPage(offset + BETA_PAGE_SIZE)}>
          <ChevronRight size={16} />
        </button>
      </nav>
    </section>
  );
}

export function seoulTimestamp(value: string): string {
  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul", year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23"
  }).format(new Date(value));
}
