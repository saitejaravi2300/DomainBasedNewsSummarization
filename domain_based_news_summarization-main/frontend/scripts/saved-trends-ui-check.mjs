import { chromium } from 'playwright';

const stamp = Date.now();
const email = `qa.savedui.${stamp}@example.com`;
const password = 'VerifyPass123!';
const name = 'QA Saved UI';

const registerRes = await fetch('http://localhost:8000/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password, name }),
});
if (!registerRes.ok) throw new Error(`Register failed: ${registerRes.status}`);
const registerData = await registerRes.json();

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  storageState: {
    cookies: [],
    origins: [
      {
        origin: 'http://localhost:3000',
        localStorage: [
          { name: 'authToken', value: registerData.token },
          { name: 'user_id', value: registerData.user?.id || '' },
        ],
      },
    ],
  },
});
const page = await context.newPage();

await page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded' });
await page.getByRole('button', { name: /Generate digest/i }).first().click();
await page.locator('h3.text-lg.font-semibold').first().waitFor({ timeout: 120000 });

const firstTrendTitle = ((await page.locator('h3.text-lg.font-semibold').first().textContent()) || '').trim();

const firstCard = page.locator('div.group.relative').first();
await firstCard.locator('button:has(svg.lucide-bookmark)').first().click();
await page.waitForTimeout(800);

await page.goto('http://localhost:3000/saved', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(1200);

const savedCards = await page.locator('h3.text-lg.font-semibold').count();
const savedTitle = savedCards ? (((await page.locator('h3.text-lg.font-semibold').first().textContent()) || '').trim()) : '';

console.log(JSON.stringify({
  firstTrendTitle,
  savedCards,
  savedTitle,
  titleMatch: Boolean(firstTrendTitle && savedTitle && firstTrendTitle === savedTitle),
}, null, 2));

await context.close();
await browser.close();
