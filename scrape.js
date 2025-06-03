const axios = require("axios");
const cheerio = require("cheerio");
const fs = require("fs");

const HEADERS = {
  "User-Agent":
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " +
    "(KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36",
  "Accept-Language": "en-US,en;q=0.5",
};

const archiveUrl =
  "http://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/fourd_result_draw_list_en.html";

async function fetchAllDraws(numOfRounds = 0, scrapeAll = false) {
  try {
    // Step 1: Fetch the archive page with all draw dates
    const { data: archiveHtml } = await axios.get(archiveUrl, { headers: HEADERS });
    const $archive = cheerio.load(archiveHtml);

    // Step 2: Extract <option> elements inside <select> (dates)
    const options = [];
    $archive("select option").each((i, el) => {
      const querystring = $(el).attr("querystring");
      if (querystring) options.push(querystring);
    });

    const results = [];
    let count = 0;

    for (const querystring of options) {
      if (!scrapeAll && count >= numOfRounds) break;

      // Step 3: Construct URL for each draw result page
      const drawUrl = `http://www.singaporepools.com.sg/en/4d/Pages/Results.aspx?${querystring}`;

      try {
        const { data: drawHtml } = await axios.get(drawUrl, { headers: HEADERS });
        const $draw = cheerio.load(drawHtml);

        // Step 4: Extract prizes (use selectors analogous to your XPath)
        // 1st, 2nd, 3rd prizes are in <td class="tdFirstPrize"> etc.
        const firstPrize = $draw("td.tdFirstPrize").first().text().trim();
        const secondPrize = $draw("td.tdSecondPrize").first().text().trim();
        const thirdPrize = $draw("td.tdThirdPrize").first().text().trim();

        // Starter prizes (tbody with class tbodyStarterPrizes > td)
        const starterPrizes = [];
        $draw("tbody.tbodyStarterPrizes td").each((i, el) => {
          starterPrizes.push($(el).text().trim());
        });

        // Consolation prizes (tbody with class tbodyConsolationPrizes > td)
        const consolationPrizes = [];
        $draw("tbody.tbodyConsolationPrizes td").each((i, el) => {
          consolationPrizes.push($(el).text().trim());
        });

        results.push({
          url: drawUrl,
          firstPrize,
          secondPrize,
          thirdPrize,
          starterPrizes,
          consolationPrizes,
        });

        console.log(`Scraped draw #${count + 1}: ${drawUrl}`);

        count++;
      } catch (err) {
        console.warn(`Failed to fetch draw at ${drawUrl}: ${err.message}`);
      }
    }

    // Step 5: Save results to JSON file
    fs.writeFileSync("4d_all_results.json", JSON.stringify(results, null, 2));
    console.log(`✅ Finished scraping ${count} draws.`);
  } catch (err) {
    console.error("❌ Scraping failed:", err.message);
  }
}

// Usage: scrape 10 rounds, scrapeAll = false
fetchAllDraws(10, false);
