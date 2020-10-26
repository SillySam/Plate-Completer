package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"strings"

	"github.com/gocolly/colly"
)

// Cars found in a crawl
type CrawlResult struct {
	Found []Vehicle
}

// Scrapped car information
type Vehicle struct {
	Plate        string
	Confirmation string `json:"confirmation"`
	Model        string `json:"model"`
	Submodel     string `json:"submodel"`
	Year         string `json:"vehicle_year"`
	Color        string `json:"colour"`
}

func getPlates() []string {
	data, _ := ioutil.ReadFile("plates.txt")
	content := string(data)

	content = strings.TrimPrefix(content, `[`)
	content = strings.TrimSuffix(content, "]")
	content = strings.ReplaceAll(content, `'`, "")

	list := strings.Split(content, ",")

	return list
}

func convertToVehicle(data string, plate string) Vehicle {
	// Get raw JSON string and covert to vehicle struct
	var vehicle Vehicle
	err := json.Unmarshal([]byte(data), &vehicle)
	if err != nil {
		fmt.Println(err.Error())
	}
	vehicle.Plate = plate
	return vehicle
}

func formatURL(plate string) string {
	// Substitute in plate to URL
	return "https://rightcar.govt.nz/_ws/get_rc2_mob.aspx?callback=callback&params={%22service%22%3A%22recall%22%2C%22plate%22%3A%22" +
		plate + "%22%2C%22browse%22%3Afalse%2C%22e%22%3A%22m%22}"
}

func crawlPage(plate string, out chan CrawlResult) {

	result := CrawlResult{}
	result.Found = make([]Vehicle, 0)

	c := colly.NewCollector()

	c.OnHTML("body", func(e *colly.HTMLElement) {
		// Get raw json from string
		htmlResponce := e.Text
		filtered := strings.TrimPrefix(htmlResponce, `callback({"vehicle":[`)
		filtered = strings.TrimSuffix(filtered, "]})")

		// Convert to struct
		vehicle := convertToVehicle(filtered, plate)

		if vehicle.Confirmation == "ok" {
			result.Found = append(result.Found, vehicle)
		}
	})

	c.OnError(func(_ *colly.Response, err error) {
		fmt.Println("Something went wrong:", err)
	})

	c.Visit(formatURL(plate))
	out <- result
}

func getPlateCount(out chan int) {
	out <- len(getPlates()) - 1
}

func main() {

	cars := make([]Vehicle, 0)
	countChan := make(chan int, 1)

	getPlateCount(countChan)

	count := <-countChan

	resultChan := make(chan CrawlResult, count)

	plates := getPlates()

	// start scrapping
	for i := 0; i < count; i++ {
		go crawlPage(plates[i+1], resultChan)
	}

	// wait for results
	for i := 0; i < count; i++ {
		result := <-resultChan

		// add found to total
		cars = append(cars, result.Found...)

		// update progress bar
		bars := int((20.00 / float64(count)) * float64(i+1))
		progress := "[" + strings.Repeat("#", bars)
		progress += strings.Repeat(" ", 20-bars) + "]"
		fmt.Print("\r" + progress)
	}

	// jsonify the cars
	carsJson, err := json.MarshalIndent(cars, "", "\t")
	if err != nil {
		panic("Failed to jsonify the cars")
	}
	// write saved json
	ioutil.WriteFile("cars.json", carsJson, 0644)

	fmt.Println("\n\nDone")
}
