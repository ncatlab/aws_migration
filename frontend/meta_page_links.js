function is_historical_page() {
  return window.location.pathname.includes("/history/show")
}

function edit_page_link() {
  return "<a href=\"../edit?page_name=" +
      document.title +
      "\">Edit</a>"
}

function discuss_page_link_bottom() {
  return "<a id=\"discuss_page_bottom\" href=\"#\">Discuss</a>"
}

function source_page_link() {
  return "<a href=\"" +
    window.location.toString().replace("/show/", "/source/") +
    "\">Source</a>"
}

function set_discuss_page_link() {
  fetch(
      DISCUSSION_THREAD_ROOT_URL + document.title)
    .then(response => {
      if (response.status != 200) {
        return FORUM_ROOT_URL
      }
      return response.text()
    })
    .then(discussion_thread_link => {
      document.getElementById("discuss_page_bottom").href = discussion_thread_link
    })
}

function history_page_link(is_historical) {
  if (is_historical) {
    return "<a href=\"../../all/" +
      document.title +
      "\">History</a>"
  } else {
    return "<a href=\"../history/all/" +
      document.title +
      "\">History</a>"
  }
}

function current_page_link() {
  return "<a href=\"../../../show/" +
    document.title +
    "\">Current</a>"
}

function bottom_menu() {
  var is_historical = is_historical_page()
  var menu_items = []
  if (!is_historical) {
    menu_items.push(edit_page_link())
  } else {
    menu_items.push(current_page_link())
  }
  menu_items.push(discuss_page_link_bottom())
  menu_items.push(history_page_link(is_historical))
  menu_items.push(source_page_link())
  document.getElementById("menu_separator").style.display = "block"
  document.getElementById("bottom_menu").innerHTML = menu_items.join(" ")
  set_discuss_page_link()
}

document.addEventListener("DOMContentLoaded", function () {
  bottom_menu()
})
