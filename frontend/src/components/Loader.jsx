// Full-screen animated loader. Render it conditionally: {busy && <Loader />}
export default function Loader() {
    return (
      <div className="loading" role="status" aria-live="polite">
        Loading&#8230;
      </div>
    );
  }