import { Fragment, useRef, useEffect, useState } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { ChevronDown, Building2, Check } from 'lucide-react';
import { useCompanyContext } from '@/app/providers/CompanyContext';
import clsx from 'clsx';
import { createPortal } from 'react-dom';

// Helper function to get company initials
function getCompanyInitials(businessName: string): string {
  const words = businessName.split(' ').filter(word => word.length > 0);
  if (words.length === 1) {
    return words[0].substring(0, 2).toUpperCase();
  }
  return words.slice(0, 2).map(word => word[0]).join('').toUpperCase();
}

export function CompanySelector() {
  const { availableCompanies, selectedCompanyId, selectedCompany, setSelectedCompany } = useCompanyContext();
  const buttonRef = useRef<HTMLButtonElement>(null);
  const [dropdownPosition, setDropdownPosition] = useState({ top: 0, left: 0 });
  const [useInitials, setUseInitials] = useState(false);
  const nameRef = useRef<HTMLSpanElement>(null);

  // Check if we need to show initials based on available space
  useEffect(() => {
    const checkSpace = () => {
      if (nameRef.current && buttonRef.current) {
        const buttonWidth = buttonRef.current.offsetWidth;
        const nameWidth = nameRef.current.scrollWidth;
        // If the name is wider than 80% of button width, use initials
        setUseInitials(nameWidth > buttonWidth * 0.8);
      }
    };

    checkSpace();
    window.addEventListener('resize', checkSpace);
    return () => window.removeEventListener('resize', checkSpace);
  }, [selectedCompany]);

  // Don't show selector if only one company
  if (availableCompanies.length <= 1) {
    const displayName = selectedCompany?.business_name
      ? (useInitials ? getCompanyInitials(selectedCompany.business_name) : selectedCompany.business_name)
      : 'Cargando...';

    return (
      <h3
        ref={nameRef}
        className="text-base font-bold text-slate-900 dark:text-slate-100 truncate min-w-0 max-w-full"
        title={selectedCompany?.business_name} // Show full name on hover
      >
        {displayName}
      </h3>
    );
  }

  // Update dropdown position when menu opens
  const updatePosition = () => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect();
      setDropdownPosition({
        top: rect.bottom + 8, // 8px margin-top (mt-2)
        left: rect.left,
      });
    }
  };

  return (
    <Menu as="div" className="relative inline-block text-left min-w-0 max-w-full">
      {({ open }) => {
        // Update position when menu opens
        if (open && buttonRef.current) {
          requestAnimationFrame(updatePosition);
        }

        const displayName = selectedCompany?.business_name
          ? (useInitials ? getCompanyInitials(selectedCompany.business_name) : selectedCompany.business_name)
          : 'Seleccionar empresa';

        return (
          <>
            <Menu.Button
              ref={buttonRef}
              className="inline-flex items-center gap-2 rounded-lg px-0 py-0 text-base font-bold text-slate-900 dark:text-slate-100 hover:text-emerald-700 dark:hover:text-emerald-400 transition-colors justify-start min-w-0 max-w-full w-full"
              onClick={updatePosition}
              title={selectedCompany?.business_name} // Show full name on hover
            >
              <span ref={nameRef} className="truncate text-left flex-1 min-w-0">
                {displayName}
              </span>
              <ChevronDown className="h-4 w-4 flex-shrink-0" aria-hidden="true" />
            </Menu.Button>

            {open && createPortal(
              <Transition
                show={open}
                as={Fragment}
                enter="transition ease-out duration-100"
                enterFrom="transform opacity-0 scale-95"
                enterTo="transform opacity-100 scale-100"
                leave="transition ease-in duration-75"
                leaveFrom="transform opacity-100 scale-100"
                leaveTo="transform opacity-0 scale-95"
              >
                <Menu.Items
                  static
                  className="fixed w-80 origin-top-left rounded-lg bg-white dark:bg-slate-800 shadow-xl ring-1 ring-slate-200 dark:ring-slate-700 focus:outline-none"
                  style={{
                    top: `${dropdownPosition.top}px`,
                    left: `${dropdownPosition.left}px`,
                    zIndex: 9999,
                  }}
                >
          <div className="py-1">
            <div className="px-3 py-2 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
              Tus empresas
            </div>
            {availableCompanies.map((company) => (
              <Menu.Item key={company.id}>
                {({ active }) => (
                  <button
                    onClick={() => setSelectedCompany(company.id)}
                    className={clsx(
                      'group flex w-full items-center justify-between px-3 py-2 text-sm transition-colors',
                      active && 'bg-slate-50 dark:bg-slate-700/50',
                      selectedCompanyId === company.id && 'bg-emerald-50 dark:bg-emerald-900/20'
                    )}
                  >
                    <div className="flex flex-col items-start min-w-0 flex-1">
                      <span
                        className={clsx(
                          'font-medium truncate max-w-full',
                          selectedCompanyId === company.id
                            ? 'text-emerald-900 dark:text-emerald-400'
                            : 'text-slate-900 dark:text-slate-100'
                        )}
                      >
                        {company.business_name}
                      </span>
                      {company.trade_name && company.trade_name !== company.business_name && (
                        <span className="text-xs text-slate-500 dark:text-slate-400 truncate max-w-full">
                          {company.trade_name}
                        </span>
                      )}
                      <span className="text-xs text-slate-400 dark:text-slate-500 mt-0.5">
                        RUT: {company.rut}
                      </span>
                    </div>
                    {selectedCompanyId === company.id && (
                      <Check className="h-4 w-4 text-emerald-600 dark:text-emerald-400 flex-shrink-0 ml-2" />
                    )}
                  </button>
                )}
              </Menu.Item>
            ))}
                  </div>
                </Menu.Items>
              </Transition>,
              document.body
            )}
          </>
        );
      }}
    </Menu>
  );
}
