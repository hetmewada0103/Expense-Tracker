// Run when page loads
document.addEventListener("DOMContentLoaded", pageLoaded);

function pageLoaded() {
    // Tooltip initialization (Bootstrap)
    var tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');

    for (var i = 0; i < tooltipElements.length; i++) {
        new bootstrap.Tooltip(tooltipElements[i]);
    }
    // Hide floating button on some pages
    var path = window.location.pathname;

    if (path.indexOf("profile") !== -1 ||
        path.indexOf("logout") !== -1 ||
        path.indexOf("login") !== -1 ||
        path.indexOf("signup") !== -1) {

        var btn = document.querySelector(".btn-floating");

        if (btn != null) {
            btn.style.display = "none";
        }
    }
}

// Format Currency
function formatCurrency(amount, currency) {

    var symbol = currency;

    if (currency == "USD") symbol = "$";
    if (currency == "EUR") symbol = "€";
    if (currency == "GBP") symbol = "£";
    if (currency == "INR") symbol = "₹";
    if (currency == "JPY") symbol = "¥";

    amount = parseFloat(amount);
    amount = amount.toFixed(2);

    return symbol + " " + amount;
}

// Format Date
function formatDate(dateString) {

    var date = new Date(dateString);

    var options = {
        year: "numeric",
        month: "short",
        day: "numeric"
    };

    return date.toLocaleDateString("en-US", options);
}

// Button Loading State
function setLoadingState(button, isLoading) {

    if (isLoading == true) {
        button.disabled = true;
        button.innerHTML = "Loading...";
    } else {
        button.disabled = false;

        var original = button.getAttribute("data-original-text");

        if (original != null) {
            button.innerHTML = original;
        } else {
            button.innerHTML = "Submit";
        }
    }
}


// Update Expense Function
function updateExpense() {

    var id = document.getElementById("expense_id").value;
    var amount = document.getElementById("amount").value;
    var category = document.getElementById("category").value;
    var description = document.getElementById("description").value;

    fetch("/update_expense/" + id, {
        method: "PUT",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            amount: amount,
            category: category,
            description: description
        })
    })
    .then(function(response) {
        return response.json();
    })
    .then(function(data) {
        alert(data.message);
        location.reload();
    });
}
