const axios = require("axios");
const cheerio = require("cheerio");
const fs = require("fs");

async function fetch4D() {
  try {
    const url = "https://www.singaporepools.com.sg/en/product/Pages/4d_results.aspx";
    const { data } = await axios.get(url, {
      headers: { "User-Agent": "Mozilla/5.0" },
    });

    const $ = cheerio.load(data);

    const result = {
      date: $(".result_draw_date").first().text().trim(),
      firstPrize: $(".fourd_firstPrize .fourd_winningNo").first().text().trim(),
      secondPrize: $(".fourd_secondPrize .fourd_winningNo").first().text().trim(),
      thirdPrize: $(".fourd_thirdPrize .fourd_winningNo").first().text().trim(),
      starterPrizes: [],
      consolationPrizes: [],
      updatedAt: new Date().toISOString(),
    };

    $(".starter span.fourd_winningNo").each((_, el) => {
      result.starterPrizes.push($(el).text().trim());
    });

    $(".consolation span.fourd_winningNo").each((_, el) => {
      result.consolationPrizes.push($(el).text().trim());
    });

    fs.writeFileSync("4d.json", JSON.stringify(result, null, 2));
    console.log("✅ 4D results scraped and saved.");
  } catch (err) {
    console.error("❌ Scraping failed:", err.message);
  }
}

fetch4D();
