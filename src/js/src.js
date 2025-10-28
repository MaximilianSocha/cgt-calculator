let sessionId = null;
let stripe = null;
let elements = null;
let cardElement = null;
let clientSecret = null;

// Initialize Stripe
async function initStripe() {
  const response = await fetch("/api/config");
  const config = await response.json();
  stripe = Stripe(config.stripePublishableKey);
  elements = stripe.elements();
  cardElement = elements.create("card");
  cardElement.mount("#card-element");

  cardElement.on("change", function (event) {
    const displayError = document.getElementById("card-errors");
    if (event.error) {
      displayError.textContent = event.error.message;
    } else {
      displayError.textContent = "";
    }
  });
}

initStripe();

function toggleDropdown(element) {
  const dropdown = element.parentElement;
  dropdown.classList.toggle("active");
}

// document.getElementById("fileInput").addEventListener("click", function () {
//   document.getElementById("fileInput").click();
// });

document
  .getElementById("fileInput")
  .addEventListener("change", async function (e) {
    const file = e.target.files[0];
    if (!file) return;

    const uploadBtn = document.getElementById("fileInput");
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<span class="spinner"></span> Processing...';

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (response.ok) {
        sessionId = data.session_id;
        document.getElementById("successMessage").innerHTML = `
                        <p>${data.message}</p>
                        <p style="margin-top: 1rem;"><strong>Years Processed:</strong> ${
                          data.summary.years_processed
                        }</p>
                        <p><strong>Financial Years:</strong> ${data.summary.financial_years.join(
                          ", "
                        )}</p>
                    `;
        document.getElementById("successModal").style.display = "block";
      } else {
        alert("Error: " + data.error);
      }
    } catch (error) {
      alert("Error uploading file: " + error.message);
    } finally {
      uploadBtn.disabled = false;
      uploadBtn.textContent = "Import your csv file and calculate!";
      e.target.value = "";
    }
  });

function closeModal() {
  document.getElementById("successModal").style.display = "none";
  sessionId = null;
}

async function proceedToPayment() {
  document.getElementById("successModal").style.display = "none";

  try {
    const response = await fetch("/api/create-payment-intent", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ session_id: sessionId }),
    });

    const data = await response.json();

    if (response.ok) {
      clientSecret = data.clientSecret;
      document.getElementById("paymentModal").style.display = "block";
    } else {
      alert("Error creating payment: " + data.error);
    }
  } catch (error) {
    alert("Error: " + error.message);
  }
}

function closePaymentModal() {
  document.getElementById("paymentModal").style.display = "none";
}

document
  .getElementById("payment-form")
  .addEventListener("submit", async function (e) {
    e.preventDefault();

    const payBtn = document.getElementById("payBtn");
    payBtn.disabled = true;
    payBtn.innerHTML = '<span class="spinner"></span> Processing...';

    try {
      const { error, paymentIntent } = await stripe.confirmCardPayment(
        clientSecret,
        {
          payment_method: {
            card: cardElement,
          },
        }
      );

      if (error) {
        document.getElementById("card-errors").textContent = error.message;
        payBtn.disabled = false;
        payBtn.textContent = "Pay $9.99";
      } else if (paymentIntent.status === "succeeded") {
        // Verify payment and get download link
        const verifyResponse = await fetch("/api/verify-payment", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            payment_intent_id: paymentIntent.id,
            session_id: sessionId,
          }),
        });

        const verifyData = await verifyResponse.json();

        if (verifyResponse.ok) {
          // Close modal and trigger download
          document.getElementById("paymentModal").style.display = "none";

          // Trigger download
          window.location.href = verifyData.download_url;

          // Show success message
          alert("Payment successful! Your download will begin shortly.");

          // Reset
          sessionId = null;
          payBtn.disabled = false;
          payBtn.textContent = "Pay $9.99";
        } else {
          alert("Error verifying payment: " + verifyData.error);
          payBtn.disabled = false;
          payBtn.textContent = "Pay $9.99";
        }
      }
    } catch (error) {
      alert("Payment error: " + error.message);
      payBtn.disabled = false;
      payBtn.textContent = "Pay $9.99";
    }
  });
