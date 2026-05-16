import { chromium } from 'playwright';

const stamp = Date.now();
const email = `qa.customdel.${stamp}@example.com`;
const password = 'VerifyPass123!';
const name = 'QA Custom Del';

const registerRes = await fetch('http://localhost:8000/auth/register', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password, name }),
});
if (!registerRes.ok) throw new Error(`Register failed: ${registerRes.status}`);
const registerData = await registerRes.json();
const token = registerData.token;

const createRes = await fetch('http://localhost:3000/api/custom-domains', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  },
  body: JSON.stringify({
    domain_name: 'Delete Me Domain',
    description: 'temp',
    keywords: 'delete me domain',
  }),
});
if (!createRes.ok) throw new Error(`Create custom domain failed: ${createRes.status}`);

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  storageState: {
    cookies: [],
    origins: [
      {
        origin: 'http://localhost:3000',
        localStorage: [
          { name: 'authToken', value: token },
          { name: 'user_id', value: registerData.user?.id || '' },
        ],
      },
    ],
  },
});

const page = await context.newPage();
await page.goto('http://localhost:3000/dashboard', { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(1000);

const beforeCount = await page.getByRole('button', { name: /Delete Me Domain/i }).count();
const pillContainer = page.locator('div.group.relative').filter({ hasText: 'Delete Me Domain' }).first();
await pillContainer.hover();
await page.getByRole('button', { name: /Remove Delete Me Domain/i }).first().click();
await page.waitForTimeout(1200);
const afterCount = await page.getByRole('button', { name: /Delete Me Domain/i }).count();

console.log(JSON.stringify({ beforeCount, afterCount, removed: beforeCount > 0 && afterCount === 0 }, null, 2));

await context.close();
await browser.close();
