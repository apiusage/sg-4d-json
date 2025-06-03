const axios = require("axios");
const cheerio = require("cheerio");
const fs = require("fs");

async function fetch4D() {
  try {
    const url = "https://www.singaporepools.com.sg/en/product/pages/4d_results.aspx";

    const { data } = await axios.get(url, {
      headers: {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
      }
    });

    const $ = cheerio.load(data);

    const result = {
      date: $(".drawDate").first().text().trim(),
      firstPrize: $(".result1 span").first().text().trim(),
      secondPrize: $(".result2 span").first().text().trim(),
      thirdPrize: $(".result3 span").first().text().trim(),
      starterPrizes: [],
      consolationPrizes: [],
      updatedAt: new Date().toISOString()
    };

    $(".fourDStarter span").each((_, el) => {
      const val = $(el).text().trim();
      if (val) result.starterPrizes.push(val);
    });

    $(".fourDConsolation span").each((_, el) => {
      const val = $(el).text().trim();
      if (val) result.consolationPrizes.push(val);
    });

    fs.writeFileSync("4d.json", JSON.stringify(result, null, 2));
    console.log("✅ Scraped and saved to 4d.json");
  } catch (err) {
    console.error("❌ Scrape failed:", err.message);
  }
}

fetch4D();
