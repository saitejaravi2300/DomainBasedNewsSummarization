import { chromium } from 'playwright';

const stamp = Date.now();
const email = `qa.switch.${stamp}@example.com`;
const password = 'VerifyPass123!';
const name = 'QA Switch';

const registerRes = await fetch('http://localhost:8000/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password, name }),
});

if (!registerRes.ok) {
  throw new Error(`Register failed: ${registerRes.status}`);
}

const registerData = await registerRes.json();
const token = registerData.token;
const userId = registerData.user?.id || '';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  storageState: {
    cookies: [],
    origins: [
      {
        origin: 'http://localhost:3000',
        localStorage: [
          { name: 'authToken', value: token },
          { name: 'user_id', value: userId },
        ],
      },
    ],
  },
});

const page = await context.newPage();
await page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded' });

await page.getByRole('button', { name: /Generate digest/i }).first().click();
await page.locator('h3.text-lg.font-semibold').first().waitFor({ timeout: 120000 });

const aiTitle = ((await page.locator('h3.text-lg.font-semibold').first().textContent()) || '').trim();

await page.getByRole('button', { name: 'Finance' }).click();
await page.waitForTimeout(700);
const financeCards = await page.locator('h3.text-lg.font-semibold').count();

await page.getByRole('button', { name: /AI & ML/i }).first().click();
await page.waitForTimeout(700);
const aiCardsBack = await page.locator('h3.text-lg.font-semibold').count();
const aiTitleBack = aiCardsBack
  ? (((await page.locator('h3.text-lg.font-semibold').first().textContent()) || '').trim())
  : '';

console.log(
  JSON.stringify(
    {
      aiTitle,
      financeCards,
      aiCardsBack,
      aiTitleBack,
      sameTitleRestored: Boolean(aiTitle && aiTitle === aiTitleBack),
    },
    null,
    2
  )
);

await context.close();
await browser.close();
