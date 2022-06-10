function render_includes() {
  const page_inclusions = document.getElementsByClassName("page_inclusion")
  if (page_inclusions === undefined || page_inclusions.length == 0) {
    contents_and_environment_numbering()
    equation_numbering()
    environment_and_equation_references()
    render_context_menu()
    return
  }
  for (var i=0; i < page_inclusions.length; i++) {
    const page_inclusion_div = page_inclusions[i]
    const page_name = page_inclusion_div.dataset.pageToInclude
    fetch(PAGES_ROOT_URL + page_name)
      .then(response => {
        if (response.status != 200) {
          return ""
        }
        return response.text()
      })
      .then(page_to_include => {
        if (page_to_include) {
          page_inclusion_div.style.paddingTop = "0em"
          page_inclusion_div.innerHTML = page_to_include.split("<span class=\"page_content_start\"></span>")[1].split("<span class=\"page_content_end\"></span>")[0]
        }
        contents_and_environment_numbering()
        equation_numbering()
        environment_and_equation_references()
        render_context_menu()
      })
  }
}

document.addEventListener("DOMContentLoaded", function () {
  render_includes()
})
