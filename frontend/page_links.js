function page_links() {
  /*
  var links = document.getElementsByTagName("a")
  for (let element of links) {
    if (element.className != "page_link") {
      continue
    }

    element.onclick = function (event) {
      var page_name = element.href.substring(element.href.lastIndexOf('/') + 1)
      var page_exists_request = new XMLHttpRequest();
      page_exists_request.open("HEAD", "./" + page_name, false);
      page_exists_request.onload = function () {
        if (page_exists_request.status == 200) {
          return
        } else {
          var redirect_request = new XMLHttpRequest();
          redirect_request.open("GET", "../redirect/" + page_name, false);
          redirect_request.onload = function() {
            if (redirect_request.status == 200) {
              var redirect_name = redirect_request.responseText
              event.target.href = "./" + redirect_name
            } else {
              event.target.href = "../new/" + page_name
            }
          }
          redirect_request.send(null);
        }
      }
      page_exists_request.send(null);
    }
  }
  */
}

document.addEventListener("DOMContentLoaded", function () {
  page_links()
})
