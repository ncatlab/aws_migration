function prepare_for_preview(preview_html) {
  document.getElementById("preview_separator").style.display = "block"
  document.getElementById("preview").innerHTML = preview_html.getElementsByTagName("div")[1].innerHTML
  document.getElementById("preview").style.marginTop = "-4em"
  var table_of_contents = document.getElementById("table_of_contents")
  if (table_of_contents != null) {
    table_of_contents.style.paddingTop = "0em"
  }
  document.getElementsByClassName("search")[0].remove()
  render_includes()
  var context_menu = document.getElementById("context_menu")
  if (context_menu != null) {
    for (const div of context_menu.getElementsByTagName("div")) {
      div.style.paddingTop = "0em"
    }
  }
}

function preview_edit() {
  clear_submit_error_messages()
  document.getElementById("edit_preview").removeAttribute("edit_preview_succeeded")
  if (!document.getElementById("title").hasAttribute("page_found")) {
    return false
  } else if (!document.getElementById("edit_source").value.trim()) {
    return false
  } else if (!document.getElementById("author").value.trim()) {
    document.getElementById("submit_error_messages").innerHTML =
      "Please provide a name in the 'Author' field. Typically, nLab authors use their full, real name. If you do not wish to provide your name, please use 'Anonymous' (without the quotation marks)."
    document.getElementById("submit_error_messages").style.display = "block"
    return false
  }
  document.getElementById("preview").innerHTML = ""
  document.getElementById("preview_separator").style.display = "none"
  document.getElementById("edit_submit").style.display = "none"
  document.getElementById("edit_preview").style.display = "none"
  document.getElementById("submit").classList.add("spinner")
  fetch(
    RENDER_PREVIEW_ROOT_URL,
    {
      "method": "PUT",
      "body": JSON.stringify({
        "author": document.getElementById("author").value.trim(),
        "page_name": document.getElementById("title").getAttribute("page_name"),
        "source": document.getElementById("edit_source").value
      })
    })
  .then(response => {
    if (response.status != 200) {
      document.getElementById("submit").classList.remove("spinner")
      document.getElementById("edit_preview").style.display = "inline-block"
      document.getElementById("edit_submit").style.display = "inline-block"
    } else {
      document.getElementById("edit_preview").setAttribute("edit_preview_succeeded", "")
    }
    return response.text()
  })
  .then(responseText => {
    if (document.getElementById("edit_preview").hasAttribute("edit_preview_succeeded")) {
      var preview_html = document.createElement("html")
      preview_html.innerHTML = responseText
      prepare_for_preview(preview_html)
      location.href = "#preview"
    } else {
      document.getElementById("submit_error_messages").innerText = responseText
      document.getElementById("submit_error_messages").style.display = "block"
      location.href = "#submit_error_messages"
    }
    document.getElementById("submit").classList.remove("spinner")
    document.getElementById("edit_preview").style.display = "inline-block"
    document.getElementById("edit_submit").style.display = "inline-block"
  })
}

document.addEventListener("DOMContentLoaded", function () {
  document.getElementById("edit_preview").addEventListener("click", preview_edit)
})
