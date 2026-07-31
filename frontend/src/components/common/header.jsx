export function BasisCardHeader({ icon, title, }) {
    return (<div className="flex items-center gap-2.5 mb-1">
      <div className="w-7 h-7 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
        {icon}
      </div>
      <h3 className="font-semibold text-slate-800 text-sm">
        {title}
      </h3>
    </div>);
}