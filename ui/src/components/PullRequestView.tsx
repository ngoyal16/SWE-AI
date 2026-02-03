import React from 'react';

interface PullRequestViewProps {
    prLink: string;
}

const PullRequestView: React.FC<PullRequestViewProps> = ({ prLink }) => (
    <button style={{ padding: '10px 15px', backgroundColor: '#007bff', color: 'white', borderRadius: '5px', cursor: 'pointer', border: 'none', margin: '10px 0' }} onClick={() => window.open(prLink, '_blank')}>View PR</button>
);

export default PullRequestView;