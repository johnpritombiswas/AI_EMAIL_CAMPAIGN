const apiStatus = document.querySelector("#apiStatus");
const readyStatus = document.querySelector("#readyStatus");
const recipientCount = document.querySelector("#recipientCount");
const helperText = document.querySelector("#helperText");
const resultBox = document.querySelector("#resultBox");
const campaignList = document.querySelector("#campaignList");
const readyBtn = document.querySelector("#readyBtn");
const gmailBtn = document.querySelector("#gmailBtn");
const customersBtn = document.querySelector("#customersBtn");
const subjectsBtn = document.querySelector("#subjectsBtn");
const bodiesBtn = document.querySelector("#bodiesBtn");
const campaignBtn = document.querySelector("#campaignBtn");
const manualForm = document.querySelector("#manualForm");
const manualTo = document.querySelector("#manualTo");
const manualSubject = document.querySelector("#manualSubject");
const manualBody = document.querySelector("#manualBody");
const sendManualBtn = document.querySelector("#sendManualBtn");
const sendSelectedBtn = document.querySelector("#sendSelectedBtn");
const template = document.querySelector("#emailCardTemplate");

let campaign = [];

async function requestJson(url, options) {
  const response = await fetch(url, options);
  const text = await response.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch (error) {
    data = { raw: text };
  }

  if (!response.ok) {
    throw new Error(data.detail ? JSON.stringify(data.detail, null, 2) : `${response.status} ${response.statusText}`);
  }
  return data;
}

function setBusy(button, label) {
  const original = button.textContent;
  button.textContent = label;
  button.disabled = true;
  return () => {
    button.textContent = original;
    button.disabled = false;
  };
}

function showResult(data) {
  resultBox.textContent = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  resultBox.classList.add("visible");
}

function emptyCampaignItem(customer) {
  return {
    name: customer.name || "Customer",
    email: customer.email || "",
    subject_line: customer.subject_line || "",
    body: customer.body || "",
  };
}

function ensureCampaignFromCustomers(customers) {
  campaign = customers.map(emptyCampaignItem);
  renderCampaign();
}

function updateCampaignByName(items, fields) {
  if (campaign.length === 0) {
    campaign = items.map((item) => emptyCampaignItem(item));
  }

  items.forEach((item, index) => {
    const target =
      campaign.find((entry) => entry.email && item.email && entry.email === item.email) ||
      campaign.find((entry) => entry.name === item.name) ||
      campaign[index];

    if (!target) {
      campaign.push(emptyCampaignItem(item));
      return;
    }

    fields.forEach((field) => {
      if (item[field] !== undefined) {
        target[field] = item[field];
      }
    });
  });

  renderCampaign();
}

function syncCampaignFromCards() {
  [...campaignList.querySelectorAll(".email-card")].forEach((card) => {
    const index = Number(card.dataset.index);
    if (!campaign[index]) {
      return;
    }
    campaign[index].subject_line = card.querySelector(".subject-input").value;
    campaign[index].body = card.querySelector(".body-input").value;
  });
}

function renderCampaign() {
  campaignList.innerHTML = "";
  recipientCount.textContent = String(campaign.length);
  sendSelectedBtn.disabled = campaign.length === 0;

  campaign.forEach((item, index) => {
    const node = template.content.cloneNode(true);
    const card = node.querySelector(".email-card");
    const checkbox = node.querySelector("input[type='checkbox']");
    const label = node.querySelector(".select-row span");
    const subject = node.querySelector(".subject-input");
    const body = node.querySelector(".body-input");

    card.dataset.index = String(index);
    checkbox.checked = true;
    label.textContent = `${item.name} <${item.email || "no email"}>`;
    subject.value = item.subject_line || "";
    body.value = item.body || "";
    campaignList.append(node);
  });
}

async function checkHealth() {
  try {
    await requestJson("/health");
    apiStatus.textContent = "Online";
  } catch (error) {
    apiStatus.textContent = "Offline";
  }
}

async function checkReady() {
  const restore = setBusy(readyBtn, "Checking");
  try {
    const data = await requestJson("/ready");
    readyStatus.textContent = data.ready ? "Ready" : "Needs setup";
    showResult(data);

    if (data.ready) {
      helperText.textContent = "All required services are connected.";
    } else if (data.gmail && data.gmail.error) {
      helperText.textContent = data.gmail.error;
    } else {
      helperText.textContent = Object.entries(data.checks)
        .filter(([, ok]) => !ok)
        .map(([name]) => name.replaceAll("_", " "))
        .join(", ") || "Some checks need attention.";
    }
  } catch (error) {
    readyStatus.textContent = "Unavailable";
    helperText.textContent = error.message;
    showResult(error.message);
  } finally {
    restore();
  }
}

async function reconnectGmail() {
  const restore = setBusy(gmailBtn, "Connecting");
  helperText.textContent = "A Google sign-in window may open. Complete it, then return here.";
  try {
    const data = await requestJson("/gmail/reconnect", { method: "POST" });
    if (data.error) {
      throw new Error(data.error);
    }
    showResult(data);
    readyStatus.textContent = data.token_valid ? "Ready" : "Needs setup";
    helperText.textContent = data.token_valid ? "Gmail is connected." : "Gmail still needs reconnecting.";
  } catch (error) {
    helperText.textContent = error.message;
    showResult(error.message);
  } finally {
    restore();
    checkReady();
  }
}

async function loadRecipients() {
  const restore = setBusy(customersBtn, "Loading");
  try {
    const data = await requestJson("/customers");
    if (data.error) {
      throw new Error(data.error);
    }
    ensureCampaignFromCustomers(data.customers);
    showResult(data);
    helperText.textContent = "Recipients loaded into editable preview cards.";
  } catch (error) {
    helperText.textContent = error.message;
    showResult(error.message);
  } finally {
    restore();
  }
}

async function generateSubjects() {
  const restore = setBusy(subjectsBtn, "Generating");
  syncCampaignFromCards();
  helperText.textContent = "Generating subject lines...";
  try {
    const data = await requestJson("/subjectlines");
    if (data.error) {
      throw new Error(data.error);
    }
    updateCampaignByName(data.results, ["subject_line"]);
    showResult(data);
    helperText.textContent = "Subject lines added to the preview cards.";
  } catch (error) {
    helperText.textContent = error.message;
    showResult(error.message);
  } finally {
    restore();
  }
}

async function generateBodies() {
  const restore = setBusy(bodiesBtn, "Generating");
  syncCampaignFromCards();
  helperText.textContent = "Generating email bodies...";
  try {
    const data = await requestJson("/emailbodies");
    if (data.error) {
      throw new Error(data.error);
    }
    updateCampaignByName(data.results, ["email", "body"]);
    showResult(data);
    helperText.textContent = "Email bodies added to the preview cards.";
  } catch (error) {
    helperText.textContent = error.message;
    showResult(error.message);
  } finally {
    restore();
  }
}

async function generateCampaign() {
  const restore = setBusy(campaignBtn, "Generating");
  sendSelectedBtn.disabled = true;
  helperText.textContent = "Generating subject lines and email bodies...";
  try {
    const data = await requestJson("/campaign");
    if (data.error) {
      throw new Error(data.error);
    }
    campaign = data.results.map(emptyCampaignItem);
    renderCampaign();
    showResult(data);
    helperText.textContent = "Full campaign preview is ready to edit and send.";
  } catch (error) {
    helperText.textContent = error.message;
    showResult(error.message);
  } finally {
    restore();
    sendSelectedBtn.disabled = campaign.length === 0;
  }
}

async function sendManualEmail() {
  if (!manualForm.reportValidity()) {
    return;
  }

  if (!window.confirm("Send this email now?")) {
    return;
  }

  const restore = setBusy(sendManualBtn, "Sending");
  try {
    const result = await requestJson("/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        to: manualTo.value.trim(),
        subject: manualSubject.value.trim(),
        body: manualBody.value.trim(),
      }),
    });

    if (result.error) {
      throw new Error(result.error);
    }
    helperText.textContent = `Sent email to ${manualTo.value.trim()}.`;
    showResult(result);
  } catch (error) {
    helperText.textContent = error.message;
    showResult(error.message);
  } finally {
    restore();
  }
}

async function sendSelected() {
  syncCampaignFromCards();

  if (!window.confirm("Send the selected emails now?")) {
    return;
  }

  const restore = setBusy(sendSelectedBtn, "Sending");
  const cards = [...campaignList.querySelectorAll(".email-card")];
  let sent = 0;

  try {
    for (const card of cards) {
      const checkbox = card.querySelector("input[type='checkbox']");
      if (!checkbox.checked) {
        continue;
      }

      const index = Number(card.dataset.index);
      const item = campaign[index];

      const result = await requestJson("/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          to: item.email,
          subject: item.subject_line,
          body: item.body,
        }),
      });

      if (result.error) {
        throw new Error(result.error);
      }
      sent += 1;
    }

    helperText.textContent = `Sent ${sent} email${sent === 1 ? "" : "s"}.`;
  } catch (error) {
    helperText.textContent = error.message;
    showResult(error.message);
  } finally {
    restore();
  }
}

readyBtn.addEventListener("click", checkReady);
gmailBtn.addEventListener("click", reconnectGmail);
customersBtn.addEventListener("click", loadRecipients);
subjectsBtn.addEventListener("click", generateSubjects);
bodiesBtn.addEventListener("click", generateBodies);
campaignBtn.addEventListener("click", generateCampaign);
sendManualBtn.addEventListener("click", sendManualEmail);
sendSelectedBtn.addEventListener("click", sendSelected);

checkHealth();
checkReady();
