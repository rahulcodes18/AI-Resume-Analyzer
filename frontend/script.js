console.log("SCRIPT LOADED");

document.addEventListener("DOMContentLoaded", function () {

    const analyzeButton = document.getElementById("analyzeButton");

    analyzeButton.addEventListener("click", analyzeResume);

});


async function analyzeResume() {

    const resumeInput = document.getElementById("resumeFile");
    const targetRoleInput = document.getElementById("targetRole");
    const result = document.getElementById("result");
    const loading = document.getElementById("loading");

    const resumeFile = resumeInput.files[0];
    const targetRole = targetRoleInput.value.trim();


    if (!resumeFile) {
        result.innerText = "Please choose your Resume PDF file.";
        return;
    }


    if (targetRole === "") {
        result.innerText = "Please enter your target role.";
        return;
    }


    const formData = new FormData();

    formData.append("resume", resumeFile);
    formData.append("target_role", targetRole);


    loading.style.display = "block";
    result.innerText = "";


    try {

        const response = await fetch(
            "https://ai-resume-analyzer-1-b2pu.onrender.com/run",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        loading.style.display = "none";


        if (data.status === "success") {
            result.innerText = data.result;
        } else {
            result.innerText =
                data.message || "Something went wrong while analyzing the resume.";
        }

    } catch (error) {

        loading.style.display = "none";

        result.innerText =
            "Error connecting to Resume Analyzer: " + error.message;
    }
}