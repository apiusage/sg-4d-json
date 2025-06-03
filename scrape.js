const axios = require("axios");
const cheerio = require("cheerio");
const fs = require("fs");

const HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
  "Accept-Language": "en-US,en;q=0.5",
};

async function fetchDrawList() {
  const startUrl =
    "http://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/fourd_result_draw_list_en.html";

  try {
    const { data } = await axios.get(startUrl, { headers: HEADERS });
    const $ = cheerio.load(data);

    const queryStrings = [];
    $("select option").each((_, el) => {
      const queryString = $(el).attr("querystring");
      if (queryString) queryStrings.push(queryString);
    });

    return queryStrings;
  } catch (error) {
    console.error("Error fetching draw list:", error.message);
    return [];
  }
}

async function fetchDrawResult(queryString) {
  const url = `http://www.singaporepools.com.sg/en/4d/Pages/Results.aspx?${queryString}`;

  try {
    const { data } = await axios.get(url, { headers: HEADERS });
    const $ = cheerio.load(data);

    const date = $("span.drawDate").text().trim();
    const drawNumber = $("span.drawNumber").text().trim();
    const firstPrize = $("td.tdFirstPrize").text().trim();
    const secondPrize = $("td.tdSecondPrize").text().trim();
    const thirdPrize = $("td.tdThirdPrize").text().trim();

    const starterPrizes = [];
    $("tbody.tbodyStarterPrizes td").each((_, el) => {
      starterPrizes.push($(el).text().trim());
    });

    const consolationPrizes = [];
    $("tbody.tbodyConsolationPrizes td").each((_, el) => {
      consolationPrizes.push($(el).text().trim());
    });

    return {
      date,
      drawNumber,
      firstPrize,
      secondPrize,
      thirdPrize,
      starterPrizes,
      consolationPrizes,
      updatedAt: new Date().toISOString(),
    };
  } catch (error) {
    console.error(`Error fetching draw result for ${queryString}:`, error.message);
    return null;
  }
}

async function main() {
  const numberOfRounds = 5; // Change this to scrape more
  const scrapeAll = false; // Set true to scrape all draws

  const queryStrings = await fetchDrawList();
  if (queryStrings.length === 0) {
    console.error("No draws found, exiting.");
    return;
  }

  const results = [];

  for (let i = 0; i < queryStrings.length; i++) {
    if (!scrapeAll && i >= numberOfRounds) break;

    const result = await fetchDrawResult(queryStrings[i]);
    if (result) {
      results.push(result);
      console.log(`Scraped draw for date: ${result.date}`);
    }
  }

  fs.writeFileSync("4d_results.json", JSON.stringify(results, null, 2));
  console.log("✅ All 4D results scraped and saved.");
}

main();
