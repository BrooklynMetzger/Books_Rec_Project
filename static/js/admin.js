document.getElementById("addBookForm").addEventListener("submit", function(f){

    f.preventDefault();

    
    const info ={
    
        isbn: document.getElementById("isbn").value,
        title: document.getElementById("title").value,
        author: document.getElementById("author").value,
        genre: document.getElementById("genre").value,
        language: document.getElementById("language").value,
        pages: parseInt(document.getElementById("pages").value),
        date: document.getElementById("date").value,
    };

    fetch("/add_book", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify(info)
    })
    .then(response => response.json())
    .then(data => {
        if(data.message)
        {
            alert("Book added");
            document.getElementById("addBookForm").reset();
        }
        else if (data.error)
        {
            alert("Error: " + data.error);
        }
        
    })
    .catch(error => {
        console.error("Error:", error);
        alert("Error occurred.");
    });
});
