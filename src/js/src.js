function toggleDropdown(element) {
  const dropdown = element.parentElement;
  dropdown.classList.toggle("active");
}

 document.getElementById('fileInput').addEventListener('change', function(event) {
  const selectedFiles = event.target.files;
  if (selectedFiles.length == 1) {
    const firstFile = selectedFiles[0];
    console.log("Selected file name:", firstFile.name);
    console.log("Selected file size:", firstFile.size, "bytes");
  }
});