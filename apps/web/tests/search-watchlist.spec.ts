import { test, expect } from "@playwright/test";

test("search to watchlist flow", async ({ page }) => {
  await page.setContent(`
    <input placeholder="Search" />
    <button id="add">Add</button>
    <ul id="wl"></ul>
    <script>
      const input = document.querySelector('input');
      document.getElementById('add').onclick = () => {
        const li = document.createElement('li');
        li.textContent = input.value;
        document.getElementById('wl').appendChild(li);
      };
    </script>
  `);

  await page.fill("input", "AAPL");
  await page.click("#add");
  await expect(page.locator("#wl li")).toHaveText("AAPL");
});
