document.getElementById("dataForm").addEventListener("submit", async function(e) {
    e.preventDefault();

    const job_desc = document.getElementById("job_desc").value;
    const candidate_info = document.getElementById("candidate_info").value;
    // const gpt_token = document.getElementById("gpt_token").value;
    const file_type = document.getElementById("file_type").value;

    document.getElementById("response").innerText = "Generating resume...";

    try {
        let res = await fetch("https://resume-automation-ylxh.onrender.com/submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            // body: JSON.stringify({ job_desc, candidate_info, gpt_token, file_type })
            body: JSON.stringify({ job_desc, candidate_info, file_type })
        });

        if (!res.ok) {
            document.getElementById("response").innerText = "Error generating file";
            return;
        }

        let blob = await res.blob();
        let url = URL.createObjectURL(blob);
        let a = document.createElement("a");
        a.href = url;
        a.download = file_type === "word" ? "resume.docx" : "resume.pdf";
        a.click();

        document.getElementById("response").innerHTML = `<a href="${url}" download>Click here to download</a>`;
    } catch (error) {
        document.getElementById("response").innerText = "Error connecting to server";
    }
});
