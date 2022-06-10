var context_header_set = false

function fetch_content(element) {
  var context_name = element.id.replace("context_", "").replace(/_/g, " ")
  var header_name =  element.id + "_header"
  fetch(CONTEXT_PAGES_ROOT_URL + context_name)
    .then(response => response.text())
    .then(content => {
      var parsed_content = new DOMParser().parseFromString(content, 'text/html');
      var content_element = parsed_content.querySelector("#for_display")
      if (content_element === null) {
        return
      }
      if (!context_header_set) {
        var context_menu = document.getElementById("context_menu")
        context_menu.innerHTML = "\n<h2>Context</h2>\n" + context_menu.innerHTML
        context_header_set = true
        context_menu.style.display = "block"
      }
      var context_header = document.createElement("h3")
      context_header.id = header_name
      context_header.innerText = context_name.charAt(0).toUpperCase() + context_name.slice(1)
      context_header.style.cursor = "pointer"
      context_header.onclick = function () {
        var context_content = document.getElementById(element.id + "_content")
        if (context_content.style.display === "none") {
          context_content.style.display = "block"
        } else {
          context_content.style.display = "none"
        }
      }
      var context_content = document.createElement("div")
      context_content.id = element.id + "_content"
      context_content.style.display = "none"
      context_content.innerHTML = content_element.innerHTML
      document.getElementById(element.id).appendChild(context_header)
      document.getElementById(element.id).appendChild(context_content)
  })
}

function render_context_menu() {
  var context_menu = document.getElementById("context_menu")
  if (!context_menu) {
    return
  }
  var context_menu_children = context_menu.children
  for (let i=0; i < context_menu_children.length; i++) {
    var element = context_menu_children[i]
    element.display = "none"
    fetch_content(element)
  }
}
