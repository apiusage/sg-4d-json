const axios = require('axios');
const cheerio = require('cheerio');

/**
 * @typedef {Object} DrawResult
 * @property {string} date
 * @property {string} drawNumber
 * @property {string} firstPrize
 * @property {string} secondPrize
 * @property {string} thirdPrize
 * @property {string[]} starterPrizes
 * @property {string[]} consolationPrizes
 */

/**
 * Fetch list of query strings for draws
 * @returns {Promise<string[]>}
 */
async function fetchDrawList() {
  const startUrl = 'http://www.singaporepools.com.sg/DataFileArchive/Lottery/Output/fourd_result_draw_list_en.html';
  const headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.5',
  };

  try {
    const response = await axios.get(startUrl, { headers });
    const $ = cheerio.load(response.data);
    const queryStrings = [];

    $('select option').each((_, element) => {
      const queryString = $(element).attr('querystring');
      if (queryString) {
        queryStrings.push(queryString);
      }
    });

    return queryStrings;
  } catch (error) {
    console.error('Error fetching draw list:', error);
    return [];
  }
}

/**
 * Fetch detailed draw result by query string
 * @param {string} queryString
 * @returns {Promise<DrawResult|null>}
 */
async function fetchDrawResult(queryString) {
  const url = `http://www.singaporepools.com.sg/en/4d/Pages/Results.aspx?${queryString}`;
  const headers = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.5',
  };

  try {
    const response = await axios.get(url, { headers });
    const $ = cheerio.load(response.data);

    const date = $('span.drawDate').text().trim();
    const drawNumber = $('span.drawNumber').text().trim();
    const firstPrize = $('td.tdFirstPrize').text().trim();
    const secondPrize = $('td.tdSecondPrize').text().trim();
    const thirdPrize = $('td.tdThirdPrize').text().trim();

    const starterPrizes = [];
    $('tbody.tbodyStarterPrizes td').each((_, element) => {
      starterPrizes.push($(element).text().trim());
    });

    const consolationPrizes = [];
    $('tbody.tbodyConsolationPrizes td').each((_, element) => {
      consolationPrizes.push($(element).text().trim());
    });

    return {
      date,
      drawNumber,
      firstPrize,
      secondPrize,
      thirdPrize,
      starterPrizes,
      consolationPrizes,
    };
  } catch (error) {
    console.error(`Error fetching draw result for query string ${queryString}:`, error);
    return null;
  }
}

async function main() {
  const numberOfRounds = 5; // Number of rounds to scrape
  const scrapeAll = false; // Set to true to scrape all

  const queryStrings = await fetchDrawList();
  const results = [];

  for (let i = 0; i < queryStrings.length; i++) {
    if (!scrapeAll && i >= numberOfRounds) {
      break;
    }
    const result = await fetchDrawResult(queryStrings[i]);
    if (result) {
      results.push(result);
    }
  }

  console.log(JSON.stringify(results, null, 2));
}

main();
