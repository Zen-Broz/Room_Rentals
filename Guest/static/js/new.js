document.addEventListener("DOMContentLoaded", function () {
  // Add animation classes to elements on load
  const animateElements = () => {
    document.querySelectorAll(".nav-item").forEach((item, index) => {
      item.classList.add("fadeIn");
      item.classList.add(`delay-${index + 1}`);
    });

    document.querySelectorAll(".auth-buttons .btn").forEach((btn, index) => {
      btn.classList.add("fadeIn");
      btn.classList.add(`delay-${index + 3}`);
    });
  };

  // Call animation function after a small delay
  setTimeout(animateElements, 100);

  // Navbar scroll effect
  const navWrapper = document.querySelector(".nav-wrapper");
  window.addEventListener("scroll", () => {
    if (window.scrollY > 50) {
      navWrapper.classList.add("scrolled");
    } else {
      navWrapper.classList.remove("scrolled");
    }
  });

  // Navbar toggler animation
  const toggler = document.querySelector(".custom-toggler");
  const icon = document.querySelector(".animated-icon");

  if (toggler) {
    toggler.addEventListener("click", () => {
      icon.classList.toggle("open");
    });
  }

  // Modal functionality
  const modal = document.getElementById("id01");
  const closeModal = document.querySelector(".close-modal");

  // Function to open modal
  window.openModal = function (content) {
    if (modal) {
      const modalBody = modal.querySelector(".modal-body");
      if (modalBody) {
        modalBody.innerHTML = content;
      }
      modal.style.display = "block";
      setTimeout(() => {
        modal.classList.add("show");
      }, 10);
    }
  };

  // Function to close modal
  window.closeModal = function () {
    if (modal) {
      modal.classList.remove("show");
      setTimeout(() => {
        modal.style.display = "none";
      }, 300);
    }
  };

  // Close modal with X button
  if (closeModal) {
    closeModal.addEventListener("click", closeModal);
  }

  // Close modal when clicking outside
  window.onclick = function (event) {
    if (event.target == modal) {
      closeModal();
    }
  };

  // Active navigation item
  const navItems = document.querySelectorAll(".nav-item");
  const currentPath = window.location.pathname;

  navItems.forEach((item) => {
    item.classList.remove("active");
    const link = item.querySelector(".nav-link");
    if (link && link.getAttribute("href") === currentPath) {
      item.classList.add("active");
    }
  });

  // Add ripple effect to buttons
  document.querySelectorAll(".btn").forEach((button) => {
    button.addEventListener("click", function (e) {
      const rect = button.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      const ripple = document.createElement("span");
      ripple.style.cssText = `
          position: absolute;
          background-color: rgba(255, 255, 255, 0.7);
          border-radius: 50%;
          width: 5px;
          height: 5px;
          left: ${x}px;
          top: ${y}px;
          transform: translate(-50%, -50%);
          animation: ripple-effect 0.8s linear;
          pointer-events: none;
        `;

      button.appendChild(ripple);

      setTimeout(() => {
        ripple.remove();
      }, 800);
    });
  });

  // Add ripple effect style
  const style = document.createElement("style");
  style.textContent = `
      @keyframes ripple-effect {
        0% {
          width: 0;
          height: 0;
          opacity: 0.5;
        }
        100% {
          width: 500px;
          height: 500px;
          opacity: 0;
        }
      }
    `;
  document.head.appendChild(style);

  // Intersection Observer for scroll animations
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1 }
  );

  // Add .animate-on-scroll class to elements you want to animate
  document.querySelectorAll(".animate-on-scroll").forEach((el) => {
    observer.observe(el);
  });

  // Footer social icons hover effect
  document.querySelectorAll(".social-icon").forEach((icon) => {
    icon.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-8px)";
    });

    icon.addEventListener("mouseleave", function () {
      this.style.transform = "translateY(0)";
    });
  });

  // Function to add page transition effects
  function addPageTransitions() {
    const style = document.createElement("style");
    style.textContent = `
        .page-transition {
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background-color: var(--primary-color);
          z-index: 9999;
          transform: translateY(100%);
        }
        
        .page-transition.enter {
          animation: slidePageUp 0.5s forwards;
        }
        
        .page-transition.exit {
          transform: translateY(0);
          animation: slidePageDown 0.5s forwards;
        }
        
        @keyframes slidePageUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
        
        @keyframes slidePageDown {
          from { transform: translateY(0); }
          to { transform: translateY(-100%); }
        }
      `;
    document.head.appendChild(style);

    // Create transition element
    const transitionEl = document.createElement("div");
    transitionEl.className = "page-transition";
    document.body.appendChild(transitionEl);

    // Handle link clicks for page transitions
    document.querySelectorAll('a:not([target="_blank"])').forEach((link) => {
      link.addEventListener("click", function (e) {
        const href = this.getAttribute("href");

        // Skip # links, javascript: links, or external links
        if (
          href.startsWith("#") ||
          href.startsWith("javascript:") ||
          href.startsWith("http")
        ) {
          return;
        }

        e.preventDefault();

        transitionEl.classList.add("enter");

        setTimeout(() => {
          transitionEl.classList.remove("enter");
          transitionEl.classList.add("exit");

          setTimeout(() => {
            window.location.href = href;
          }, 300);
        }, 500);
      });
    });
  }

  // Uncomment below to enable page transitions
  // addPageTransitions();
});

// Load Google Fonts
(function () {
  const link = document.createElement("link");
  link.href =
    "https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap";
  link.rel = "stylesheet";
  document.head.appendChild(link);
})();
