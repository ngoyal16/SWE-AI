import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';

interface PageHeaderContextType {
    title: string;
    description: string;
    setPageHeader: (title: string, description: string) => void;
}

const PageHeaderContext = createContext<PageHeaderContextType | undefined>(undefined);

export function PageHeaderProvider({ children }: { children: React.ReactNode }) {
    const [header, setHeader] = useState({ title: '', description: '' });

    const setPageHeader = useCallback((title: string, description: string) => {
        setHeader({ title, description });
    }, []);

    return (
        <PageHeaderContext.Provider value={{ ...header, setPageHeader }}>
            {children}
        </PageHeaderContext.Provider>
    );
}

export function usePageHeader(title: string, description: string) {
    const context = useContext(PageHeaderContext);
    if (!context) {
        throw new Error('usePageHeader must be used within a PageHeaderProvider');
    }

    useEffect(() => {
        context.setPageHeader(title, description);
    }, [title, description, context.setPageHeader]);
}

export function useHeaderContext() {
    const context = useContext(PageHeaderContext);
    if (!context) {
        throw new Error('useHeaderContext must be used within a PageHeaderProvider');
    }
    return context;
}
