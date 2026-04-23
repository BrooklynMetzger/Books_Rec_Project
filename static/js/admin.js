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
document.getElementById("updateBookForm").addEventListener("submit", function(f){

    f.preventDefault();

     const info ={
    
        isbn: document.getElementById("u_isbn").value,
        title: document.getElementById("u_title").value,
        author: document.getElementById("u_author").value,
        genre: document.getElementById("u_genre").value,
        language: document.getElementById("u_language").value,
        pages: parseInt(document.getElementById("u_pages").value),
        date: document.getElementById("u_date").value,
    };

    fetch("/update_book", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(info)
    })

    .then(response => response.json())
    .then(data => {
        if (data.message) {
            alert("Book updated");
            document.getElementById("updateBookForm").reset();
        } else if (data.error) {
            alert("Error: " + data.error);
        }
    })

    .catch(error => {
        console.error("Error:", error);
        alert("Error occurred");
    });

});
