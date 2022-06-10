function search_query() {
  const query_parameters = new Proxy(
    new URLSearchParams(window.location.search),
      {
        get: (query_parameters, key) => query_parameters.get(key),
      }
  )
  const search_query = query_parameters.query
  if (!search_query) {
    return
  }
  document.getElementById("title").setAttribute("search_query", search_query)
  document.getElementById("top_header").innerText = "Search – " + search_query
}

function search_results() {
  var search_query = document.getElementById("title").getAttribute("search_query")
  fetch(SEARCH_ROOT_URL + search_query)
    .then(response => {
      if (response.status == 200) {
        return response.json()
      } else {
        document.getElementById("title").setAttribute("error_fetching_results")
      }
    } )
    .then(results => {
      if (document.getElementById("title").hasAttribute("error_fetching_results")) {
        document.getElementById("search_results").classList.remove("spinner")
        document.getElementById("search_results").innerHTML =
          "<p>An error occurred when fetching the search results. Please raise this at the <a href=\"" +
          FORUM_ROOT_URL +
          "\">" +
          FORUM_NAME +
          "</a></p>"
        return
      } else if (results === undefined || results.length == 0) {

        document.getElementById("search_results").classList.remove("spinner")
        document.getElementById("search_results").innerHTML =
          "<p>No matching pages found.</p>"
        return
      }
      var search_results_list = document.createElement("ul")
      results.forEach(result => {
        var result_item = document.createElement("li")
        result_item.innerHTML =
          "<a href=\"" + PAGES_ROOT_URL + result + "\" class=\"page_link\">" + result + "</a>"
        search_results_list.appendChild(result_item)
      })
      document.getElementById("search_results").classList.remove("spinner")
      document.getElementById("search_results").appendChild(search_results_list)

    }
  )
}

document.addEventListener("DOMContentLoaded", function () {
  search_query()
  if (document.getElementById("title").hasAttribute("search_query")) {
    search_results("search_query")
  }
})
