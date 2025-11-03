export const NotesPanel = ({ notes }: { notes: string[] }) => (
  <section className="bg-white rounded-xl shadow-card p-5 space-y-3">
    <h3 className="text-lg font-semibold text-gray-900">Next reviews</h3>
    <ul className="space-y-2 text-sm text-gray-600">
      {notes.map((note, idx) => (
        <li key={idx} className="border border-gray-100 rounded-lg p-3 bg-gray-50">
          {note}
        </li>
      ))}
    </ul>
  </section>
);
