document.getElementById("syntax_guide_link").addEventListener("click", function () {
  var syntax_guide = document.getElementById("syntax_guide")
  if (!syntax_guide.style.display || syntax_guide.style.display == "none") {
    syntax_guide.style.display = "block"
  } else {
    syntax_guide.style.display = "none"
  }
})
