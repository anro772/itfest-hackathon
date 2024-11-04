window.loadNavbar = async function () {
  try {
    const response = await fetch("navbar.html");
    const data = await response.text();
    document.getElementById("navbar").innerHTML = data;
    initializeNavbar();
  } catch (error) {
    console.error("Error loading navbar:", error);
  }
};

window.initializeNavbar = function () {
  const userMenu = document.getElementById("userMenu");
  const loginButton = document.getElementById("loginButton");
  const usernameSpan = document.getElementById("username");
  const logoutButton = document.getElementById("logoutButton");
  const profileIcon = document.querySelector(".profile-icon");

  function updateNavbar() {
    const token = localStorage.getItem("token");
    const userData = JSON.parse(localStorage.getItem("user") || "{}");

    if (token && userData) {
      // User is logged in
      loginButton.style.display = "none";
      userMenu.style.display = "none";
      usernameSpan.textContent = userData.username || "User";
      profileIcon.style.display = "block";
    } else {
      // User is logged out
      loginButton.style.display = "block";
      userMenu.style.display = "none";
      profileIcon.style.display = "block";
    }
  }

  // Toggle user menu when clicking profile icon
  profileIcon.addEventListener("click", function (e) {
    e.stopPropagation();
    const token = localStorage.getItem("token");
    if (token) {
      userMenu.style.display =
        userMenu.style.display === "none" ? "block" : "none";
    }
  });

  // Handle logout
  logoutButton.addEventListener("click", function () {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    updateNavbar();
    window.location.href = "/login.html";
  });

  // Close menu when clicking outside
  document.addEventListener("click", function (e) {
    if (!userMenu.contains(e.target) && !profileIcon.contains(e.target)) {
      userMenu.style.display = "none";
    }
  });

  // Initial check
  updateNavbar();

  // Listen for storage events (in case of logout in another tab)
  window.addEventListener("storage", function (e) {
    if (e.key === "token" || e.key === "user") {
      updateNavbar();
    }
  });
};
