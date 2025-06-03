const axios = require("axios");
const cheerio = require("cheerio");
const fs = require("fs");

async function fetch4DResults() {
  const url = "https://www.singaporepools.com.sg/en/product/Pages/4d_results.aspx";

  try {
    const { data } = await axios.get(url, {
      headers: {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
      },
    });

    const $ = cheerio.load(data);

    const date = $(".drawDate").first().text().trim();

    const firstPrize = $(".result1 span").text().trim();
    const secondPrize = $(".result2 span").text().trim();
    const thirdPrize = $(".result3 span").text().trim();

    const starterPrizes = [];
    $(".fourDStarter span").each((_, el) => {
      starterPrizes.push($(el).text().trim());
    });

    const consolationPrizes = [];
    $(".fourDConsolation span").each((_, el) => {
      consolationPrizes.push($(el).text().trim());
    });

    const result = {
      date,
      firstPrize,
      secondPrize,
      thirdPrize,
      starterPrizes,
      consolationPrizes,
      updatedAt: new Date().toISOString(),
    };

    fs.writeFileSync("4d.json", JSON.stringify(result, null, 2));
    console.log("✅ 4D results scraped and saved to 4d.json");

  } catch (err) {
    console.error("❌ Scraping failed:", err.message);
  }
}

fetch4DResults();
