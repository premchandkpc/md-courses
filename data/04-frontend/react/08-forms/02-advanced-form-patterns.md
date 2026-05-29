# Advanced Form Patterns: State Management, Validation & Submission

**Level:** Intermediate-Advanced | **Time:** 50 mins | **Interview:** 🔥 Critical

---

## Overview

Most developers build forms wrong: duplicating validation logic, handling errors inconsistently, re-rendering too often, mixing controlled/uncontrolled inputs. This guide covers production form patterns using React Hook Form, Zod validation, async submission, error handling, and multi-step forms.

**Why this matters:**
- Forms are 80% of web apps (login, checkout, profiles, settings)
- Bad form UX = 70% cart abandonment (ecommerce)
- Interview prep: "How would you build a complex multi-step form?"
- Performance: Form re-renders are a major bottleneck

---

## 1. Form State Management Patterns

### Pattern 1: useState (Naive, Inefficient)

```javascript
// ❌ BAD: Duplicates state, re-renders per keystroke
function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [terms, setTerms] = useState(false);
  const [emailError, setEmailError] = useState('');
  const [passwordError, setPasswordError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) setEmailError('Required');
    if (!password) setPasswordError('Required');
    // ... validation, submission
  };

  return (
    <>
      <input value={email} onChange={(e) => setEmail(e.target.value)} />
      {emailError && <span>{emailError}</span>}
      {/* ... 20 more lines for password, checkbox, submit */}
    </>
  );
}

// Problems:
// - 15+ useState calls
// - Manual validation
// - Re-render on every keystroke (email → password → terms)
// - Error state separate from field state
// - No form-level submission state
```

---

### Pattern 2: useReducer (More Organized)

```javascript
// ✅ BETTER: Centralized state
function LoginForm() {
  const initialState = {
    email: '',
    password: '',
    terms: false,
    errors: {},
    loading: false,
    submitted: false
  };

  function formReducer(state, action) {
    switch (action.type) {
      case 'SET_FIELD':
        return {
          ...state,
          [action.name]: action.value,
          errors: { ...state.errors, [action.name]: '' } // Clear error on change
        };
      case 'SET_ERROR':
        return {
          ...state,
          errors: { ...state.errors, [action.name]: action.error }
        };
      case 'SET_LOADING':
        return { ...state, loading: action.loading };
      case 'SET_SUBMITTED':
        return { ...state, submitted: action.submitted };
      default:
        return state;
    }
  }

  const [state, dispatch] = useReducer(formReducer, initialState);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    dispatch({
      type: 'SET_FIELD',
      name,
      value: type === 'checkbox' ? checked : value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    dispatch({ type: 'SET_LOADING', loading: true });

    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        body: JSON.stringify({
          email: state.email,
          password: state.password
        })
      });

      if (!response.ok) {
        dispatch({
          type: 'SET_ERROR',
          name: 'email',
          error: 'Invalid credentials'
        });
      }
    } finally {
      dispatch({ type: 'SET_LOADING', loading: false });
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input name="email" value={state.email} onChange={handleChange} />
      {state.errors.email && <span>{state.errors.email}</span>}
      {/* ... */}
    </form>
  );
}

// Better but still verbose
```

---

### Pattern 3: React Hook Form (Production Standard)

```javascript
// ✅ BEST: Minimal re-renders, built-in validation
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

// Define schema (validation + types)
const loginSchema = z.object({
  email: z.string().email('Invalid email'),
  password: z.string().min(8, 'Min 8 characters'),
  terms: z.boolean().refine((v) => v === true, 'Must accept terms')
});

function LoginForm() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError
  } = useForm({
    resolver: zodResolver(loginSchema),
    mode: 'onBlur' // Validate on blur (not every keystroke)
  });

  const onSubmit = async (data) => {
    try {
      const response = await fetch('/api/login', {
        method: 'POST',
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        setError('email', {
          message: 'Invalid credentials'
        });
      }
    } catch (err) {
      setError('root', {
        message: 'Login failed'
      });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input
        {...register('email')}
        placeholder="Email"
        disabled={isSubmitting}
      />
      {errors.email && <span>{errors.email.message}</span>}

      <input
        {...register('password')}
        type="password"
        disabled={isSubmitting}
      />
      {errors.password && <span>{errors.password.message}</span>}

      <label>
        <input {...register('terms')} type="checkbox" />
        Accept terms
      </label>
      {errors.terms && <span>{errors.terms.message}</span>}

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Logging in...' : 'Login'}
      </button>

      {errors.root && <span>{errors.root.message}</span>}
    </form>
  );
}

// Advantages:
// - No useState (form lib handles state)
// - Validation (schema + lib integration)
// - Minimal re-renders (uncontrolled inputs, subscribe only to changes)
// - Built-in error handling
// - TypeScript support (inferred from schema)
```

---

## 2. Validation Patterns

### Pattern 1: Client-Side (Fast Feedback)

```javascript
// Frontend validation (Zod schema)
import { z } from 'zod';

const userSchema = z.object({
  email: z.string()
    .email('Invalid email format')
    .max(100, 'Email too long'),

  password: z.string()
    .min(8, 'Min 8 characters')
    .regex(/[A-Z]/, 'Needs uppercase')
    .regex(/[0-9]/, 'Needs number'),

  age: z.number()
    .min(18, 'Must be 18+')
    .max(120, 'Invalid age'),

  website: z.string()
    .url('Invalid URL')
    .optional() // Can be empty
});

// Usage with React Hook Form
const { register, formState: { errors } } = useForm({
  resolver: zodResolver(userSchema),
  mode: 'onChange' // Real-time validation
});
```

### Pattern 2: Server-Side (Real Validation)

```javascript
// Never trust client validation. Always validate server-side.

// Express backend
app.post('/api/register', async (req, res) => {
  try {
    // 1. Parse + validate schema
    const data = userSchema.parse(req.body);

    // 2. Check unique constraint (DB-level)
    const existingUser = await db.query(
      'SELECT id FROM users WHERE email = $1',
      [data.email]
    );
    if (existingUser.rows.length > 0) {
      return res.status(400).json({
        email: 'Email already registered'
      });
    }

    // 3. Hash password
    const hashedPassword = await bcrypt.hash(data.password, 10);

    // 4. Create user
    const user = await db.query(
      'INSERT INTO users (email, password) VALUES ($1, $2) RETURNING id',
      [data.email, hashedPassword]
    );

    return res.json({ success: true, userId: user.rows[0].id });
  } catch (err) {
    if (err instanceof z.ZodError) {
      return res.status(400).json(err.flatten().fieldErrors);
    }
    res.status(500).json({ error: 'Server error' });
  }
});

// Frontend: handle server errors
const onSubmit = async (data) => {
  const response = await fetch('/api/register', {
    method: 'POST',
    body: JSON.stringify(data)
  });

  if (!response.ok) {
    const errors = await response.json();
    // errors = { email: ['Already registered'] }
    Object.entries(errors).forEach(([field, messages]) => {
      setError(field, { message: messages[0] });
    });
  }
};
```

### Pattern 3: Real-Time Validation (Debounced)

```javascript
// Check email availability while typing (debounced)
function RegisterForm() {
  const {
    register,
    watch,
    formState: { errors },
    setError
  } = useForm({
    resolver: zodResolver(registerSchema)
  });

  const email = watch('email');

  // Debounce email uniqueness check
  useEffect(() => {
    if (!email || errors.email) return; // Wait for valid format

    const timer = setTimeout(async () => {
      const response = await fetch(`/api/check-email?email=${email}`);
      const { available } = await response.json();

      if (!available) {
        setError('email', {
          message: 'Email already registered'
        });
      }
    }, 500); // Wait 500ms after user stops typing

    return () => clearTimeout(timer);
  }, [email, errors.email, setError]);

  return (
    <form>
      <input {...register('email')} placeholder="Email" />
      {errors.email && <span>{errors.email.message}</span>}
    </form>
  );
}
```

---

## 3. Async Submission Patterns

### Pattern 1: Basic Submission

```javascript
const { handleSubmit, formState: { isSubmitting } } = useForm();

const onSubmit = async (data) => {
  try {
    const response = await fetch('/api/user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });

    if (response.ok) {
      // Success
      navigate('/dashboard');
    } else {
      const error = await response.json();
      setError('root', { message: error.message });
    }
  } catch (err) {
    setError('root', { message: 'Network error' });
  }
};

return (
  <form onSubmit={handleSubmit(onSubmit)}>
    <input {...register('name')} />
    <button disabled={isSubmitting}>
      {isSubmitting ? 'Saving...' : 'Save'}
    </button>
  </form>
);
```

### Pattern 2: Optimistic Updates

```javascript
// Update UI before server confirms
const { mutate } = useMutation({
  mutationFn: async (data) => {
    const response = await fetch('/api/user', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    return response.json();
  },
  onMutate: (newData) => {
    // Update UI immediately (optimistic)
    queryClient.setQueryData(['user'], newData);
  },
  onError: (err, newData, context) => {
    // Rollback on error
    queryClient.setQueryData(['user'], context.previousData);
  }
});

const onSubmit = (data) => {
  mutate(data); // Optimistic: UI updates instantly
};
```

### Pattern 3: Debounced Auto-Save

```javascript
// Save form automatically after 2 seconds of no changes
function EditProfileForm() {
  const { watch, handleSubmit } = useForm({
    defaultValues: async () => {
      const response = await fetch('/api/user/profile');
      return response.json();
    }
  });

  const formData = watch(); // Subscribe to all changes
  const [lastSavedData, setLastSavedData] = useState(formData);

  useEffect(() => {
    if (JSON.stringify(formData) === JSON.stringify(lastSavedData)) {
      return; // No changes
    }

    const timer = setTimeout(async () => {
      const response = await fetch('/api/user/profile', {
        method: 'PUT',
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setLastSavedData(formData);
        // Show toast: "Saved"
      }
    }, 2000); // Save 2 seconds after last keystroke

    return () => clearTimeout(timer);
  }, [formData, lastSavedData]);

  return (
    <form>
      <input {...register('name')} />
      <input {...register('bio')} />
    </form>
  );
}
```

---

## 4. Multi-Step Form Pattern

```javascript
function CheckoutForm() {
  const [step, setStep] = useState(1); // 1: Shipping, 2: Payment, 3: Review
  const { control, watch, formState: { errors } } = useForm({
    mode: 'onChange'
  });

  const formData = watch();
  const isStep1Valid = formData.address && formData.city;
  const isStep2Valid = formData.cardNumber && formData.cardCvc;

  const handleNext = () => {
    if (step === 1 && isStep1Valid) setStep(2);
    if (step === 2 && isStep2Valid) setStep(3);
  };

  const handleBack = () => {
    setStep((s) => Math.max(1, s - 1));
  };

  const onSubmit = async (data) => {
    const response = await fetch('/api/checkout', {
      method: 'POST',
      body: JSON.stringify(data)
    });
    // Handle response
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* Step 1: Shipping */}
      {step >= 1 && (
        <fieldset>
          <h3>Shipping Address</h3>
          <input {...register('address', { required: true })} />
          <input {...register('city', { required: true })} />
        </fieldset>
      )}

      {/* Step 2: Payment */}
      {step >= 2 && (
        <fieldset>
          <h3>Payment</h3>
          <input {...register('cardNumber', { required: true })} />
          <input {...register('cardCvc', { required: true })} />
        </fieldset>
      )}

      {/* Step 3: Review */}
      {step >= 3 && (
        <fieldset>
          <h3>Review Order</h3>
          <p>Shipping: {formData.address}, {formData.city}</p>
          <p>Card ending in: {formData.cardNumber.slice(-4)}</p>
        </fieldset>
      )}

      {/* Navigation */}
      <div>
        <button
          type="button"
          onClick={handleBack}
          disabled={step === 1}
        >
          Back
        </button>

        {step < 3 && (
          <button
            type="button"
            onClick={handleNext}
            disabled={step === 1 ? !isStep1Valid : !isStep2Valid}
          >
            Next
          </button>
        )}

        {step === 3 && (
          <button type="submit">
            Place Order
          </button>
        )}
      </div>
    </form>
  );
}
```

---

## 5. Custom Hooks for Forms

```javascript
// Reusable form hook
function useFormState(initialValues) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState({});
  const [touched, setTouched] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setValues((v) => ({
      ...v,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleBlur = (e) => {
    const { name } = e.target;
    setTouched((t) => ({ ...t, [name]: true }));
  };

  const validate = (validationFn) => {
    const newErrors = validationFn(values);
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (onSubmit, validationFn) => async (e) => {
    e.preventDefault();
    if (!validate(validationFn)) return;

    setIsSubmitting(true);
    try {
      await onSubmit(values);
    } finally {
      setIsSubmitting(false);
    }
  };

  return {
    values,
    errors,
    touched,
    isSubmitting,
    handleChange,
    handleBlur,
    handleSubmit
  };
}

// Usage
function LoginForm() {
  const { values, errors, handleChange, handleSubmit } = useFormState({
    email: '',
    password: ''
  });

  const validate = (values) => {
    const errors = {};
    if (!values.email) errors.email = 'Required';
    if (!values.password) errors.password = 'Required';
    return errors;
  };

  const onSubmit = async (values) => {
    await fetch('/api/login', {
      method: 'POST',
      body: JSON.stringify(values)
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit, validate)}>
      <input
        name="email"
        value={values.email}
        onChange={handleChange}
      />
      {errors.email && <span>{errors.email}</span>}
      <button type="submit">Login</button>
    </form>
  );
}
```

---

## 6. Common Mistakes

### Mistake 1: Validation Only on Submit

```javascript
// ❌ BAD: No real-time feedback
const { handleSubmit } = useForm({
  mode: 'onSubmit' // Validate only when submit clicked
});

// ✅ GOOD: Real-time validation
const { handleSubmit } = useForm({
  mode: 'onBlur' // or 'onChange' for instant feedback
});
```

### Mistake 2: Not Disabling Submit During Loading

```javascript
// ❌ BAD: Can submit twice
<button type="submit">Login</button>

// ✅ GOOD: Disable during submission
<button type="submit" disabled={isSubmitting}>
  {isSubmitting ? 'Logging in...' : 'Login'}
</button>
```

### Mistake 3: Not Validating Server-Side

```javascript
// ❌ BAD: Trust client validation
// Frontend validates, submit without checking again

// ✅ GOOD: Always validate server-side
app.post('/api/register', (req, res) => {
  // Always re-validate on backend
  const result = userSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(400).json(result.error);
  }
  // Process...
});
```

---

## 7. Performance Checklist

- [ ] Use React Hook Form (uncontrolled inputs = minimal re-renders)
- [ ] Validate on blur (not every keystroke)
- [ ] Debounce async validation (email uniqueness)
- [ ] Disable submit during submission
- [ ] Clear errors on field change
- [ ] Show loading state (spinner or disabled button)
- [ ] Handle network errors gracefully
- [ ] Validate server-side (always)
- [ ] Use Zod/Joi for schema validation
- [ ] Test form submission with React Testing Library

---

## Interview Prep Questions

1. **"How would you build a form with real-time validation?"**
   - Answer: React Hook Form with schema validation (Zod). Use mode='onChange' for instant feedback. Debounce async checks (email uniqueness) to avoid too many requests.

2. **"What's the difference between client and server validation?"**
   - Answer: Client validates for UX (instant feedback). Server validates for security (can't trust client). Always do both.

3. **"How do you handle multi-step forms?"**
   - Answer: State tracks current step. Validate only current step before moving next. On submit, validate entire form. Store data in state/Redux.

4. **"What happens if form submission fails? How do you recover?"**
   - Answer: Catch error, show error message to user. Keep form data (don't clear). Option: Retry button. Log error for debugging.

5. **"Why use React Hook Form over useState?"**
   - Answer: Fewer re-renders (uncontrolled inputs). Built-in validation. Better performance for large forms. Easier API (register, watch, handleSubmit).

---

## See Also

### Phase 7.1 Related Topics

- [Redux/Zustand Patterns](../../05-state-management/02-redux-zustand-patterns.md) — Form state management options
- [WCAG Accessibility](../../16-accessibility/02-wcag-patterns-and-compliance.md) — Form accessibility
- [XSS/CSRF/CSP](../../17-security/02-xss-csrf-csp-deep-dive.md) — CSRF token handling
- [Error Boundaries](../../35-error-handling/01-error-boundaries-and-patterns.md) — Form submission error handling

### Additional Resources

- React Hook Form: Official docs + examples
- Zod: Schema validation library
- TanStack Form: Alternative form library
- Formik: Older form library (simpler but less performant)
- Yup: Alternative to Zod for validation
