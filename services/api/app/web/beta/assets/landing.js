export function validInstallUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === "https:" && url.hostname === "expo.dev" && !url.username && !url.password && !url.port && !url.search && !url.hash &&
      /^\/accounts\/arche-trustfirstnutrition\/projects\/trust-first-nutrition\/builds\/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/.test(url.pathname);
  } catch { return false; }
}

export function validConfig(value) {
  return value && typeof value.accepting === "boolean" && value.policy_version === "2026-11-18.1" &&
    value.retention_days === 30 &&
    value.delivery === "on_page" && value.min_age === 18 && value.platform === "android";
}

export function submissionPayload(email, checks, policyVersion, website = "") {
  if (!checks.adult || !checks.android || !checks.privacy) throw new Error("consent_required");
  return { email: email.trim(), platform: "android", adult_confirmed: true, privacy_consent: true, policy_version: policyVersion, website };
}

export function failureMessage(code) {
  const messages = {
    recruitment_closed: "지금은 모집 준비 중이에요. 접수 상태를 다시 확인해 주세요.",
    recruitment_rate_limited: "잠시 신청이 몰리고 있어요. 조금 후에 다시 시도해 주세요.",
    recruitment_capacity_reached: "이번 모집 인원이 가득 찼어요. 추후 안내를 확인해 주세요.",
    recruitment_full: "이번 모집 인원이 가득 찼어요. 추후 안내를 확인해 주세요.",
    recruitment_policy_changed: "신청 안내가 바뀌었어요. 모집 상태를 다시 확인하고 동의해 주세요.",
    consent_changed: "신청 안내가 바뀌었어요. 모집 상태를 다시 확인하고 동의해 주세요.",
    invalid_application: "이메일과 참여 조건을 다시 확인해 주세요.",
    validation_error: "이메일과 참여 조건을 다시 확인해 주세요.",
  };
  return messages[code] ?? "신청을 완료하지 못했어요. 입력값은 그대로 두었으니 잠시 후 다시 시도해 주세요.";
}

function initialize() {
  const $ = (id) => document.getElementById(id);
  const form = $("beta-form"), state = $("form-state"), retry = $("config-retry"), error = $("form-error"), submit = $("submit-beta");
  let config, submitting = false, configLoading = false, installUrl = "";
  const tabs = Array.from(document.querySelectorAll("[data-tab]"));
  function activateTab(tab, focus = false) {
    for (const item of tabs) {
      const selected = item === tab;
      item.setAttribute("aria-selected", String(selected)); item.tabIndex = selected ? 0 : -1;
      $(item.getAttribute("aria-controls")).hidden = !selected;
    }
    if (focus) tab.focus();
  }
  for (const tab of tabs) {
    tab.addEventListener("click", () => activateTab(tab));
    tab.addEventListener("keydown", (event) => {
      let next;
      if (event.key === "ArrowRight") next = (tabs.indexOf(tab) + 1) % tabs.length;
      if (event.key === "ArrowLeft") next = (tabs.indexOf(tab) - 1 + tabs.length) % tabs.length;
      if (event.key === "Home") next = 0;
      if (event.key === "End") next = tabs.length - 1;
      if (next !== undefined) { event.preventDefault(); activateTab(tabs[next], true); }
    });
  }

  async function requestJson(url, options = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(url, { ...options, signal: controller.signal, credentials: "omit", cache: "no-store", headers: { Accept: "application/json", ...options.headers } });
      const value = await response.json();
      if (!response.ok) { const failure = new Error("request_failed"); failure.code = value.detail?.code; throw failure; }
      return value;
    } finally { clearTimeout(timer); }
  }

  async function loadConfig() {
    if (configLoading || submitting) return;
    configLoading = true; config = undefined; form.hidden = true; retry.hidden = true; error.hidden = true;
    state.hidden = false;
    state.textContent = "베타 모집 상태를 확인하고 있어요.";
    try {
      const value = await requestJson("/recruitment/config");
      if (!validConfig(value)) throw new Error("invalid_config");
      config = value;
      $("retention-days").textContent = String(value.retention_days);
      $("policy-version").textContent = value.policy_version;
      if (value.accepting) { state.hidden = true; form.hidden = false; }
      else { state.textContent = "베타 모집을 준비하고 있어요. 지금은 이메일을 받거나 저장하지 않습니다. 아래 문의 이메일로 궁금한 점을 알려주세요."; retry.hidden = false; }
    } catch {
      state.textContent = "모집 상태를 확인하지 못했어요. 이메일을 보내지 않았습니다. 잠시 후 다시 확인해 주세요."; retry.hidden = false;
    } finally { configLoading = false; }
  }
  retry.addEventListener("click", loadConfig);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (submitting || !config?.accepting || !form.reportValidity()) return;
    const payload = submissionPayload($("beta-email").value, {adult: $("beta-adult").checked, android: $("beta-android").checked, privacy: $("beta-privacy").checked}, config.policy_version, $("beta-website").value);
    submitting = true; submit.disabled = true; form.setAttribute("aria-busy", "true"); error.hidden = true;
    submit.textContent = "접수하고 있어요…";
    try {
      const result = await requestJson("/recruitment/applications", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)});
      if (result?.accepted !== true || result.delivery !== "on_page" || !validInstallUrl(result.install_url)) throw new Error("invalid_receipt");
      installUrl = result.install_url; $("install-link").href = installUrl;
      form.hidden = true; form.reset(); $("beta-success").hidden = false; $("beta-success").focus();
    } catch (failure) {
      error.textContent = failureMessage(failure.code); error.hidden = false;
      if (["recruitment_closed", "recruitment_policy_changed", "consent_changed"].includes(failure.code)) {
        config = undefined; retry.hidden = false;
        $("beta-privacy").checked = false;
      }
    } finally {
      submitting = false; submit.disabled = false; submit.textContent = "신청하고 설치 링크 받기 ↗"; form.removeAttribute("aria-busy");
    }
  });
  $("copy-install").addEventListener("click", async () => {
    if (!validInstallUrl(installUrl)) return;
    try { await navigator.clipboard.writeText(installUrl); $("copy-status").textContent = "설치 링크를 복사했어요."; }
    catch { $("copy-status").textContent = "복사 권한을 확인해 주세요. 위 설치 버튼을 길게 눌러 링크를 복사할 수도 있어요."; }
  });
  void loadConfig();
}

if (typeof document !== "undefined") initialize();
