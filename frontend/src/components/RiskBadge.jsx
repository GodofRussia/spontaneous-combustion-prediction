import {getRiskLabel} from '../services/dataProcessor';

const RiskBadge = ({ level }) => {
  return (
    <span className={`risk-badge badge-${level}`}>
      {getRiskLabel(level)}
    </span>
  );
};

export default RiskBadge;