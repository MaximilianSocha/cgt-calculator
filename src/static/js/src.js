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
  const appearance = {
    theme: "flat",
  };
  const options = {
    layout: {
      type: "tabs",
      defaultCollapsed: false,
    },
  };
  elements = stripe.elements({ clientSecret, appearance });
  cardElement = elements.create("payment", options);
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

document
  .getElementById("fileInput")
  .addEventListener("change", function (e) {
    const file = e.target.files[0];
    if (!file) return;

    uploadFile(e, file);
  });

async function uploadFile(e, file, allow_short_selling="") {
    const uploadBtn = document.getElementById("fileInput");
    uploadBtn.disabled = true;
    uploadBtn.innerHTML = '<span class="spinner"></span> Processing...';

    const formData = new FormData();
    formData.append("file", file);
    formData.append("allow_short_selling", allow_short_selling);

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
          <p><strong>Financial Years:</strong> ${data.summary.financial_years.join()}</p>`;
        document.getElementById("successModal").style.display = "block";
      } else if (data.short_sell_warning) {
          document.getElementById("shortSellMessage").innerHTML = `
            <p>${data.short_sell_warning}</p>
            <p>Continue calculation, or refer to instructions for more info.<p>`;
          document.getElementById("shortSellModal").style.display = "block";
          document
            .getElementById("allowShortSell")
            .addEventListener("click", function() { closeModal(); uploadFile(e, file, "True"); });
      } else if (data.symbol_error && data.lp_error) {
          document.getElementById("failMessage").innerHTML = `
            <p>${data.symbol_error}</p>
            <p>${data.lp_error}<p>`;
          document.getElementById("failureModal").style.display = "block";
      } else {
        document.getElementById("failMessage").innerHTML = `
          <p>The calculation failed with the follow error:<p>
          <p>${data.error}</p>`;
        document.getElementById("failureModal").style.display = "block";
      }
    } catch (error) {
        document.getElementById("failMessage").innerHTML = `
          <p>Error uploading file:<p>
          <p>${error.message}</p>`;
        document.getElementById("failureModal").style.display = "block";
    } finally {
      uploadBtn.disabled = false;
      uploadBtn.textContent = "Import your csv file and calculate!";
      e.target.value = "";
    }
}

function closeModal() {
  document.getElementById("successModal").style.display = "none";
  document.getElementById("failureModal").style.display = "none";
  document.getElementById("shortSellModal").style.display = "none";
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
