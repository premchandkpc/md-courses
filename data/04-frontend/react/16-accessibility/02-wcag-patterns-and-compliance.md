# WCAG 2.1: Compliance Patterns & Real-World Implementation

**Level:** Intermediate-Advanced | **Time:** 45 mins | **Interview:** 🔥 Critical

---

## Overview

WCAG 2.1 (Web Content Accessibility Guidelines) defines how to make web content usable for everyone — blind users (screen readers), motor impairments (keyboard navigation), low vision (color contrast), deaf users (captions). This isn't optional (legal liability under ADA, AODA, EAA) and improves UX for everyone.

**Why this matters:**
- 15% of global population has disability (1.3B people)
- Failed accessibility = lawsuit liability (thousands per year)
- Better a11y = better UX (keyboard nav helps power users, captions help everyone in noisy places)
- Interview prep: "How would you ensure a component is accessible?"

**Compliance levels:**
- **A:** Minimum (must pass)
- **AA:** Standard (required for public sector)
- **AAA:** Enhanced (aim for this)

---

## WCAG Principles: POUR

### P — Perceivable: Users Must See/Hear Content

#### 1. Color Contrast (WCAG AA minimum)

```javascript
// ❌ BAD: Gray on white (fails WCAG)
// Contrast ratio: 3.2:1 (needs 4.5:1 for normal text, 3:1 for large)
<div style={{ color: '#888888', backgroundColor: '#ffffff' }}>
  Form instructions
</div>

// ✅ GOOD: Dark gray on white
// Contrast ratio: 8.6:1 (passes AAA for everything)
<div style={{ color: '#222222', backgroundColor: '#ffffff' }}>
  Form instructions
</div>

// ✅ ALSO GOOD: Use established design tokens
const COLORS = {
  textPrimary: '#0F172A', // 14:1 contrast on white ✅
  textSecondary: '#475569', // 7.5:1 contrast on white ✅
  textTertiary: '#94A3B8', // 4.6:1 contrast on white ✅ (AA only)
  textInvert: '#FFFFFF' // 14:1 on dark backgrounds ✅
};

// Tool: WebAIM Contrast Checker (webaim.org/resources/contrastchecker/)
```

**Real production check:** Audit with Lighthouse (DevTools → Lighthouse) or WebAIM Color Contrast Analyzer.

---

#### 2. Alternative Text for Images

```javascript
// ❌ BAD: No alt text
<img src="/logo.png" />

// ❌ BAD: Redundant alt text
<img src="/user.png" alt="image of a person" /> {/* Obviously an image */}

// ✅ GOOD: Descriptive, purpose-driven alt
<img
  src="/user-avatar.png"
  alt="Sarah Chen, Product Manager" {/* Who? What's their role? */}
/>

// ✅ GOOD: Decorative images explicitly marked
<img
  src="/decorative-border.svg"
  alt="" {/* Empty alt = skip in screen reader */}
  aria-hidden="true"
/>

// ✅ GOOD: Complex image with longdesc fallback
<figure>
  <img
    src="/system-architecture.png"
    alt="Microservices architecture diagram"
  />
  <figcaption>
    Diagram shows API Gateway → 3 services (User, Cart, Payment) → Database
  </figcaption>
</figure>

// ✅ GOOD: Linked image (what's the link for?)
<a href="/product/shoes">
  <img src="/shoe-blue.png" alt="Blue running shoe $89" />
</a>
```

**Guidelines:**
- Decorative? Empty alt (`alt=""`)
- Functional (button, link)? Describe action ("Next page", "Close modal")
- Content (photo)? Describe what/who ("Sarah at desk", not "person.jpg")
- Complex (chart)? Use `figcaption` or nearby text

---

### O — Operable: Keyboard Navigation, No Traps

#### 1. Keyboard Navigation

```javascript
// ❌ BAD: Only mouse interaction
<div
  onClick={handleClick}
  style={{ cursor: 'pointer' }}
>
  Buy Now
</div>
// Problem: keyboard-only users can't activate

// ✅ GOOD: Use semantic HTML + keyboard events
<button onClick={handleClick}>
  Buy Now
</button>
// HTML button = keyboard accessible by default (Enter, Space)

// ✅ GOOD: Non-semantic div requires explicit handling
<div
  role="button"
  tabIndex={0}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }}
  onClick={handleClick}
>
  Buy Now
</div>

// ✅ BETTER: Use semantic HTML instead
<button type="button" onClick={handleClick}>
  Buy Now
</button>
```

**Key principle:** Use semantic HTML (`<button>`, `<a>`, `<form>`) instead of custom `<div>` elements. You get keyboard support for free.

---

#### 2. Focus Management & Visible Focus Indicators

```javascript
// ❌ BAD: Remove focus outline (breaks a11y)
button {
  outline: none; /* Don't do this! */
}

// ✅ GOOD: Keep default outline
button:focus {
  outline: 2px solid blue;
  outline-offset: 2px;
}

// ✅ GOOD: Custom focus styles (must stay visible)
button:focus-visible {
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.5);
  outline: 2px solid #4299e1;
}

// ✅ GOOD: Manage focus programmatically in modals
const Modal = ({ isOpen, onClose }) => {
  const closeButtonRef = useRef(null);
  
  useEffect(() => {
    if (isOpen) {
      // Move focus into modal when it opens
      closeButtonRef.current?.focus();
    }
  }, [isOpen]);
  
  return (
    <dialog open={isOpen}>
      <p>Modal content</p>
      <button ref={closeButtonRef} onClick={onClose}>
        Close
      </button>
    </dialog>
  );
};
```

**Tab trap prevention:**
```javascript
// ❌ BAD: User tabs into modal → tabs out of page (trap)
<Modal isOpen={true} />

// ✅ GOOD: Focus trap with dialog element
<dialog open>
  {/* All focusable elements stay within dialog */}
  {/* Browser automatically prevents tabbing out */}
</dialog>

// ✅ GOOD: Manual focus trap if needed
const useDialogTrap = (isOpen) => {
  const dialogRef = useRef(null);
  
  useEffect(() => {
    if (!isOpen) return;
    
    const dialog = dialogRef.current;
    const focusables = dialog.querySelectorAll(
      'button, [href], input, select, textarea, [tabindex]'
    );
    const first = focusables[0];
    const last = focusables[focusables.length - 1];
    
    const handleKeyDown = (e) => {
      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === first) {
          last.focus();
          e.preventDefault();
        } else if (!e.shiftKey && document.activeElement === last) {
          first.focus();
          e.preventDefault();
        }
      }
    };
    
    dialog.addEventListener('keydown', handleKeyDown);
    return () => dialog.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);
  
  return dialogRef;
};
```

---

### U — Understandable: Clear Language, Predictable Behavior

#### 1. ARIA Labels & Descriptions

```javascript
// ❌ BAD: Icon button with no label
<button>
  <SearchIcon />
</button>
// Screen reader says: "button" (what does it do?)

// ✅ GOOD: aria-label
<button aria-label="Search products">
  <SearchIcon />
</button>
// Screen reader: "Search products, button"

// ✅ GOOD: visually hidden text (screen reader only)
<button>
  <SearchIcon />
  <span className="sr-only">Search</span>
</button>

// CSS for screen-reader-only text:
const srOnly = {
  position: 'absolute',
  width: '1px',
  height: '1px',
  padding: '0',
  margin: '-1px',
  overflow: 'hidden',
  clip: 'rect(0,0,0,0)',
  whiteSpace: 'nowrap',
  borderWidth: '0'
};

// ✅ GOOD: aria-describedby for additional context
<input
  id="password"
  type="password"
  aria-describedby="pwd-hint"
/>
<div id="pwd-hint">
  Must be 8+ chars, include uppercase & number
</div>
// Screen reader reads: "password edit" → "Must be 8+ chars..."
```

---

#### 2. Form Accessibility

```javascript
// ❌ BAD: No label associated with input
<input type="email" placeholder="Email" />

// ✅ GOOD: Input with associated label
<label htmlFor="email-input">Email address</label>
<input id="email-input" type="email" />

// ✅ GOOD: Error message linked with aria-describedby
<label htmlFor="email">Email</label>
<input
  id="email"
  type="email"
  aria-describedby="email-error"
/>
{errors.email && (
  <span id="email-error" role="alert">
    {errors.email}
  </span>
)}

// ✅ GOOD: Required field marked
<label htmlFor="name">
  Name <span aria-label="required">*</span>
</label>
<input
  id="name"
  required
  aria-required="true"
/>

// Real production example: React Hook Form + accessibility
import { useForm } from 'react-hook-form';

const LoginForm = () => {
  const { register, formState: { errors } } = useForm();
  
  return (
    <form>
      <div>
        <label htmlFor="email">Email</label>
        <input
          {...register('email', { required: 'Email required' })}
          id="email"
          type="email"
          aria-describedby={errors.email ? 'email-error' : undefined}
        />
        {errors.email && (
          <span id="email-error" role="alert">
            {errors.email.message}
          </span>
        )}
      </div>
    </form>
  );
};
```

---

### R — Robust: Works with Assistive Technology (Screen Readers)

#### 1. Semantic HTML Over ARIA

```javascript
// ❌ BAD: Custom elements without semantics
<div onClick={navigate} role="navigation">
  Home | About | Contact
</div>

// ✅ GOOD: Semantic HTML
<nav>
  <a href="/">Home</a>
  <a href="/about">About</a>
  <a href="/contact">Contact</a>
</nav>

// ❌ BAD: ARIA role to fix non-semantic HTML
<div role="button" tabIndex={0} onClick={handler}>
  Click me
</div>

// ✅ GOOD: Use semantic button
<button onClick={handler}>Click me</button>

// Semantic HTML elements screen readers understand:
// <header>, <nav>, <main>, <article>, <aside>, <footer>
// <section>, <h1-h6>, <form>, <button>, <a>, <label>
// <input>, <textarea>, <select>, <table>, <th>, <td>
```

---

#### 2. ARIA Live Regions (Real-time Updates)

```javascript
// ❌ BAD: Status update, no alert
const [status, setStatus] = useState('');

const handleClick = async () => {
  setStatus('Saving...');
  await save();
  setStatus('Saved!');
};

// Screen reader may not announce the change

// ✅ GOOD: aria-live for dynamic content
const [status, setStatus] = useState('');

return (
  <div
    aria-live="polite"
    aria-atomic="true"
    role="status"
  >
    {status}
  </div>
);

// Live region types:
// aria-live="polite" — announce when user pauses (less intrusive)
// aria-live="assertive" — interrupt immediately (errors, alerts)
// aria-atomic="true" — read whole region, not just changes
// role="status" — implies aria-live="polite"
// role="alert" — implies aria-live="assertive"

// Real example: Loading spinner
const LoadingSpinner = ({ isLoading }) => (
  <div
    role="status"
    aria-live="polite"
  >
    {isLoading && "Loading..."}
  </div>
);
```

---

## Real Production Example: Accessible Card Component

```javascript
// ❌ BAD: Visual only, no semantics
function ProductCard({ product, onSelect }) {
  return (
    <div onClick={() => onSelect(product)}>
      <img src={product.image} />
      <h3>{product.name}</h3>
      <p>${product.price}</p>
    </div>
  );
}

// ✅ GOOD: Semantic, keyboard accessible, screen reader friendly
function ProductCard({ product, onSelect }) {
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onSelect(product);
    }
  };

  return (
    <article
      role="option"
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onClick={() => onSelect(product)}
      style={{
        outline: '2px solid transparent',
        outlineOffset: '2px'
      }}
      onFocus={(e) => {
        e.currentTarget.style.outline = '2px solid #4299e1';
      }}
      onBlur={(e) => {
        e.currentTarget.style.outline = '2px solid transparent';
      }}
    >
      <img
        src={product.image}
        alt={`${product.name} - ${product.price}`}
      />
      <h3>{product.name}</h3>
      <p aria-label={`Price: $${product.price}`}>
        ${product.price}
      </p>
      <span className="sr-only">
        Select {product.name} for ${product.price}
      </span>
    </article>
  );
}
```

---

## Accessibility Checklist

- [ ] Contrast ratio ≥ 4.5:1 for normal text (WebAIM checker)
- [ ] All images have descriptive alt text
- [ ] All buttons/links reachable with keyboard (Tab, Enter, Space)
- [ ] Focus indicator visible (don't remove outline)
- [ ] Form inputs have associated `<label>` elements
- [ ] Error messages linked with `aria-describedby`
- [ ] Modal focus trapped, returns after close
- [ ] Use semantic HTML (`<button>`, `<nav>`, `<main>`) not `<div role="...">
- [ ] ARIA labels only when semantic HTML doesn't apply
- [ ] Live regions (`aria-live="polite"`) for dynamic content
- [ ] Test with screen reader (NVDA free, JAWS paid, VoiceOver on Mac)
- [ ] Run Lighthouse audit (DevTools)
- [ ] Test keyboard-only navigation (no mouse)

---

## Testing Tools

| Tool | Type | Free? | Best for |
|------|------|-------|----------|
| **Lighthouse** | Automated | Yes | Quick audit in DevTools |
| **WAVE** | Visual overlay | Yes | Identifying issues on page |
| **Axe DevTools** | Automated | Yes | Deep accessibility scan |
| **NVDA** | Screen reader | Yes | Real keyboard-only testing |
| **VoiceOver** | Screen reader | Yes (Mac) | Native assistive tech |
| **WebAIM Checker** | Contrast | Yes | Color contrast validation |

---

## Interview Prep Questions

1. **"How would you make a custom dropdown accessible?"**
   - Answer: Use `<select>` native if possible. If custom: button + role="listbox", arrow keys, focus management, aria-expanded.

2. **"What's the difference between aria-label and aria-labelledby?"**
   - Answer: `aria-label` is direct string. `aria-labelledby` references another element's id (links to existing text).

3. **"Why is semantic HTML better than ARIA?"**
   - Answer: Semantic HTML has built-in keyboard support, screen reader support, and reduces ARIA burden. ARIA is fallback.

4. **"How do you ensure a modal is accessible?"**
   - Answer: Trap focus inside, alert on open, return focus on close, inert background, aria-modal="true".

5. **"Can you remove outline from buttons?"**
   - Answer: No (breaks keyboard users). Custom outline styles OK, but must be visible with 3px minimum.

---

## See Also

- WCAG 2.1 Specification (w3.org/WAI/WCAG21/quickref/)
- Web Accessibility Initiative (w3.org/WAI/)
- A11y Project Checklist (a11yproject.com)
- Inclusive Components (inclusive-components.design)
- MDN: Web Accessibility (developer.mozilla.org/en-US/docs/Web/Accessibility)
