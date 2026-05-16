import { chromium } from 'playwright';

const URL = 'http://localhost:3000/dashboard';
const BACKEND_URL = 'http://localhost:8000';

function result(id, title, pass, evidence, details = '') {
  return { id, title, pass, evidence, details };
}

function isDisplayDate(text) {
  return /^\d{2}\s[A-Za-z]{3}\s\d{4}$/.test((text || '').trim());
}

function isLikelyUsefulSoWhat(text) {
  const t = (text || '').trim();
  if (t.length < 80) return false;
  return /(action|track|monitor|impact|priority|roadmap|decision|follow-up|next)/i.test(t);
}

function isTldrNotCut(text) {
  const t = (text || '').trim();
  if (!t) return false;
  if (/[,:;\-]$/.test(t)) return false;
  if (/\.\.\.$/.test(t)) return true;
  if (/[.!?]$/.test(t)) return true;
  const words = t.split(/\s+/);
  return words.length >= 8;
}

const browser = await chromium.launch({ headless: true });
const checks = [];

async function getAuthContext() {
  const stamp = Date.now();
  const email = `qa.verify.${stamp}@example.com`;
  const password = 'VerifyPass123!';
  const name = 'QA Verifier';

  const registerRes = await fetch(`${BACKEND_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, name }),
  });

  if (registerRes.ok) {
    const data = await registerRes.json();
    return { token: data.token, userId: data.user?.id || '' };
  }

  const loginRes = await fetch(`${BACKEND_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!loginRes.ok) {
    throw new Error(`Auth bootstrap failed: register=${registerRes.status}, login=${loginRes.status}`);
  }
  const data = await loginRes.json();
  return { token: data.token, userId: data.user?.id || '' };
}

const auth = await getAuthContext();
const context = await browser.newContext({
  storageState: {
    cookies: [],
    origins: [
      {
        origin: 'http://localhost:3000',
        localStorage: [
          { name: 'authToken', value: auth.token },
          { name: 'user_id', value: auth.userId },
        ],
      },
    ],
  },
});
const page = await context.newPage();

try {
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });

  const generateBtn = page.getByRole('button', { name: /Generate digest/i }).first();
  await generateBtn.click();

  // Wait until at least one trend card is rendered.
  await page.locator('h3.text-lg.font-semibold').first().waitFor({ timeout: 120000 });
  await page.waitForTimeout(1200);

  const firstCard = page.locator('h3.text-lg.font-semibold').first().locator('xpath=ancestor::div[contains(@class,"group") and contains(@class,"relative")]').first();

  // 1) Date format check in timeline (dd Mon yyyy)
  await firstCard.getByRole('button', { name: /Story evolution/i }).click();
  const firstTimelineDate = (await firstCard.locator('p.text-xs.text-muted-foreground').first().textContent()) || '';
  checks.push(
    result(
      'date-format',
      'Dates are correctly displayed as dd Mon yyyy',
      isDisplayDate(firstTimelineDate),
      `First timeline date: "${firstTimelineDate.trim()}"`,
      'Expected format example: 03 Apr 2026'
    )
  );

  // 2) Show more reveals additional useful matter
  const summaryBlock = firstCard.locator('div.text-sm.leading-relaxed.whitespace-pre-line.break-words').first();
  const beforeSummary = ((await summaryBlock.textContent()) || '').trim();
  const readMoreBtn = firstCard.getByRole('button', { name: /Read more/i });
  let showMorePass = false;
  let showMoreEvidence = 'No Read more button found (summary may already be full-length).';

  if (await readMoreBtn.count()) {
    await readMoreBtn.first().click();
    await page.waitForTimeout(250);
    const afterSummary = ((await summaryBlock.textContent()) || '').trim();
    showMorePass = afterSummary.length > beforeSummary.length + 20;
    showMoreEvidence = `Summary length before: ${beforeSummary.length}, after: ${afterSummary.length}`;
  } else {
    // If no toggle exists, consider pass only when summary is short and not truncated.
    showMorePass = beforeSummary.length <= 360;
  }

  checks.push(
    result(
      'show-more',
      'Show more expands to additional summary content',
      showMorePass,
      showMoreEvidence,
      'Failure indicates expansion may not be surfacing more text.'
    )
  );

  // 3) TLDR/subheading not cut mid-thought
  const tldrText = ((await firstCard.locator('p.mt-3.text-muted-foreground.break-words').first().textContent()) || '').trim();
  checks.push(
    result(
      'tldr-cutoff',
      'TLDR/subheading is not cut off mid-sentence',
      isTldrNotCut(tldrText),
      `TLDR: "${tldrText}"`,
      'Heuristic fails on endings like trailing comma/colon/hyphen.'
    )
  );

  // 4) So What is actionable/useful
  const soWhatText = ((await firstCard.locator('div.mt-4.rounded-lg.border-l-4 p').nth(1).textContent()) || '').trim();
  checks.push(
    result(
      'so-what',
      'So What contains actionable guidance',
      isLikelyUsefulSoWhat(soWhatText),
      `So What: "${soWhatText}"`,
      'Checks for action-oriented terms and minimum specificity length.'
    )
  );
} catch (err) {
  checks.push(result('runner', 'Browser verification script executed', false, String(err)));
} finally {
  await context.close();
  await browser.close();
}

const passed = checks.filter((c) => c.pass).length;
const total = checks.length;

console.log(JSON.stringify({
  url: URL,
  timestamp: new Date().toISOString(),
  passed,
  total,
  checks,
}, null, 2));
