function contents_and_environment_numbering() {
  var table_of_contents = document.getElementById("table_of_contents")
  if (!table_of_contents) {
    return
  }
  var table_of_contents_list = document.createElement("ol")
  table_of_contents.appendChild(table_of_contents_list)
  var sections = document.querySelectorAll("h2, h3, h4, h5, h6, span.definition_environment, span.theorem_environment")
  var section_counters = [ 0, 0, 0, 0, 0 ]
  var theorem_counter = 0
  sections.forEach(element => {
    if (element.tagName === "SPAN") {
      theorem_counter += 1
      element.id = "theorem" + section_counters[0] + "." + theorem_counter
      element.innerText = element.innerText + " " + section_counters[0] + "." + theorem_counter
      element.setAttribute("theorem_number", section_counters[0] + "." + theorem_counter)
      return
    }
    var header_depth = element.tagName[1]
    if (element.id == "contents_header") {
      return
    } else if (header_depth == 2) {
      section_counters[0] += 1
      for (var i=1; i < 4; i++) {
        section_counters[i] = 0
      }
      theorem_counter = 0
      element.id = "section-" + section_counters[0]
      table_of_contents_list.innerHTML += "\n<li id=\"table_of_contents_section-" + section_counters[0] + "\"><a href=\"#section-" + section_counters[0] + "\">" + element.innerHTML + "</a></li>\n"
      element.innerText = section_counters[0] + ". " + element.innerText

    } else if (section_counters[header_depth - 2] == 0) {
      section_counters[header_depth - 2] = 1
      for (var i=header_depth-1; i < 5; i++) {
        section_counters[i] = 0
      }
      var table_of_contents_parent = document.getElementById("table_of_contents_section-" + section_counters.slice(0, header_depth - 2).join("-"))
      var element_id = section_counters.slice(0, header_depth - 1).join("-")
      element.id = "section-" + element_id
      table_of_contents_parent.innerHTML += "\n<ul id=\"table_of_contents_section-" + section_counters.slice(0, header_depth - 2).join("-") + "_list\">\n<li id=\"table_of_contents_section-" + element_id + "\"><a href=\"#section-" + element_id + "\">" + element.innerHTML + "</a></li>\n</ul>\n"
    } else {
      for (var i=header_depth-1; i < 5; i++) {
        section_counters[i] = 0
      }
      var table_of_contents_parent = document.getElementById("table_of_contents_section-" + section_counters.slice(0, header_depth - 2).join("-") + "_list")
      section_counters[header_depth - 2] += 1
      var element_id = section_counters.slice(0, header_depth - 1).join("-")
      element.id = "section-" + element_id
      table_of_contents_parent.innerHTML += "<li id=\"table_of_contents_section-" + element_id + "\"><a href=\"#section-" + element_id + "\">" + element.innerHTML + "</a></li>\n"
    }
  })
}

function environment_and_equation_references() {
  document.querySelectorAll("a.environment_or_equation_reference").forEach(element => {
    var environment_or_equation_id = element.getAttribute("href").substr(1);
    var environment_or_equation = document.getElementById(environment_or_equation_id);
    if (environment_or_equation == null) {
      console.log("No environment or equation with label '" + environment_or_equation_id + "'")
      return "?"
    }
    if (environment_or_equation.tagName == "DIV") {
      var theorem_number = environment_or_equation.querySelector("span").getAttribute("theorem_number")
      element.innerText = theorem_number
    } else if ((environment_or_equation.tagName == "SPAN") && (environment_or_equation.hasAttribute("data-latex"))) {
      var equation_number = environment_or_equation.getAttribute("equation_number")
      element.innerText = equation_number
    } else {
      console.log("No environment or equation with label '" + environment_or_equation_id + "'")
      return "?"
    }
    if (element.innerText.trim() == "") {
      console.log("No environment or equation with label '" + environment_or_equation_id + "'")
      return "?"
    }
  })
}

function equation_numbering() {
  var counter = 0
  document.querySelectorAll("span.katex-display").forEach(element => {
    counter += 1
    var equation_span = document.createElement("SPAN")
    equation_span.classList.add("equation")
    equation_span.innerText = "(" + counter + ")"
    element.parentNode.setAttribute("equation_number", counter)
    element.parentNode.insertBefore(equation_span, element)
  })
}
