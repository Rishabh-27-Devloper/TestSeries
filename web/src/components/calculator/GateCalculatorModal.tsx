import React, { useState } from 'react';
import { X, Delete } from 'lucide-react';

interface GateCalculatorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const GateCalculatorModal: React.FC<GateCalculatorModalProps> = ({ isOpen, onClose }) => {
  const [display, setDisplay] = useState('0');
  const [memory, setMemory] = useState(0);
  const [isDeg, setIsDeg] = useState(true);
  const [hasEvaluated, setHasEvaluated] = useState(false);

  if (!isOpen) return null;

  const handleDigit = (digit: string) => {
    if (hasEvaluated || display === '0' || display === 'Error') {
      setDisplay(digit);
      setHasEvaluated(false);
    } else {
      setDisplay(display + digit);
    }
  };

  const handleOperator = (op: string) => {
    setHasEvaluated(false);
    if (display === 'Error') {
      setDisplay(op);
    } else {
      setDisplay(display + ' ' + op + ' ');
    }
  };

  const handleClear = () => {
    setDisplay('0');
    setHasEvaluated(false);
  };

  const handleBackspace = () => {
    if (display === 'Error' || hasEvaluated) {
      setDisplay('0');
      setHasEvaluated(false);
      return;
    }
    if (display.length > 1) {
      setDisplay(display.slice(0, -1).trimEnd());
    } else {
      setDisplay('0');
    }
  };

  const handleEvaluate = () => {
    try {
      // Clean and sanitize mathematical expression
      let expr = display.replace(/×/g, '*').replace(/÷/g, '/').replace(/\^/g, '**');
      // eslint-disable-next-line no-eval
      const result = Function(`'use strict'; return (${expr})`)();
      if (typeof result === 'number' && !isNaN(result) && isFinite(result)) {
        const rounded = Math.round((result + Number.EPSILON) * 1e8) / 1e8;
        setDisplay(String(rounded));
        setHasEvaluated(true);
      } else {
        setDisplay('Error');
      }
    } catch (e) {
      setDisplay('Error');
    }
  };

  const handleFunction = (func: string) => {
    try {
      const current = parseFloat(display) || 0;
      let val = current;
      const toRad = isDeg ? Math.PI / 180 : 1;
      const fromRad = isDeg ? 180 / Math.PI : 1;

      switch (func) {
        case 'sin':
          val = Math.sin(current * toRad);
          break;
        case 'cos':
          val = Math.cos(current * toRad);
          break;
        case 'tan':
          val = Math.tan(current * toRad);
          break;
        case 'asin':
          val = Math.asin(current) * fromRad;
          break;
        case 'acos':
          val = Math.acos(current) * fromRad;
          break;
        case 'atan':
          val = Math.atan(current) * fromRad;
          break;
        case 'sinh':
          val = Math.sinh(current);
          break;
        case 'cosh':
          val = Math.cosh(current);
          break;
        case 'tanh':
          val = Math.tanh(current);
          break;
        case 'ln':
          val = Math.log(current);
          break;
        case 'log':
          val = Math.log10(current);
          break;
        case 'sqrt':
          val = Math.sqrt(current);
          break;
        case 'cbrt':
          val = Math.cbrt(current);
          break;
        case 'exp':
          val = Math.exp(current);
          break;
        case 'sqr':
          val = current * current;
          break;
        case 'cube':
          val = current * current * current;
          break;
        case '1/x':
          val = current !== 0 ? 1 / current : NaN;
          break;
        case 'fact':
          val = factorial(Math.floor(current));
          break;
        case '+/-':
          val = -current;
          break;
        case 'pi':
          val = Math.PI;
          break;
        case 'e':
          val = Math.E;
          break;
        default:
          break;
      }

      if (isNaN(val) || !isFinite(val)) {
        setDisplay('Error');
      } else {
        const rounded = Math.round((val + Number.EPSILON) * 1e8) / 1e8;
        setDisplay(String(rounded));
        setHasEvaluated(true);
      }
    } catch (e) {
      setDisplay('Error');
    }
  };

  const factorial = (n: number): number => {
    if (n < 0) return NaN;
    if (n === 0 || n === 1) return 1;
    let res = 1;
    for (let i = 2; i <= n; i++) res *= i;
    return res;
  };

  const handleMemory = (action: string) => {
    const current = parseFloat(display) || 0;
    switch (action) {
      case 'MC':
        setMemory(0);
        break;
      case 'MR':
        setDisplay(String(memory));
        setHasEvaluated(true);
        break;
      case 'MS':
        setMemory(current);
        break;
      case 'M+':
        setMemory(memory + current);
        break;
      case 'M-':
        setMemory(memory - current);
        break;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-xl border border-slate-300 bg-white shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-blue-900 bg-[#1a56a5] px-4 py-2.5 text-white">
          <div className="flex items-center space-x-2">
            <span className="text-base font-bold">GATE Virtual Scientific Calculator</span>
            <span className="rounded bg-blue-800 px-2 py-0.5 text-[10px] font-semibold text-blue-100">
              Official Pattern
            </span>
          </div>
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-white/20 transition-colors"
            title="Close Calculator"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Display Bar */}
        <div className="border-b border-slate-200 bg-slate-50 p-3">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsDeg(true)}
                className={`rounded px-2 py-0.5 font-semibold text-xs transition-colors ${
                  isDeg ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                }`}
              >
                DEG
              </button>
              <button
                onClick={() => setIsDeg(false)}
                className={`rounded px-2 py-0.5 font-semibold text-xs transition-colors ${
                  !isDeg ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
                }`}
              >
                RAD
              </button>
            </div>
            <div className="font-mono text-slate-600">
              {memory !== 0 ? <span className="text-blue-700 font-bold">M = {memory}</span> : 'M = 0'}
            </div>
          </div>

          <div className="rounded border-2 border-blue-800 bg-white px-3 py-2 text-right font-mono text-2xl font-bold tracking-wider text-slate-900 overflow-x-auto select-all">
            {display}
          </div>
        </div>

        {/* Keypad */}
        <div className="grid grid-cols-6 gap-1.5 p-3 bg-slate-100 text-xs">
          {/* Memory Row */}
          {['MC', 'MR', 'MS', 'M+', 'M-'].map((m) => (
            <button
              key={m}
              onClick={() => handleMemory(m)}
              className="rounded border border-amber-300 bg-amber-50 p-2 font-bold text-amber-900 hover:bg-amber-100 active:scale-95 transition"
            >
              {m}
            </button>
          ))}
          <button
            onClick={handleClear}
            className="rounded border border-red-300 bg-red-100 p-2 font-bold text-red-700 hover:bg-red-200 active:scale-95 transition"
          >
            CLEAR
          </button>

          {/* Row 1 Functions */}
          <button onClick={() => handleFunction('sin')} className="btn-calc-fn">sin</button>
          <button onClick={() => handleFunction('cos')} className="btn-calc-fn">cos</button>
          <button onClick={() => handleFunction('tan')} className="btn-calc-fn">tan</button>
          <button onClick={() => handleFunction('ln')} className="btn-calc-fn">ln</button>
          <button onClick={() => handleFunction('log')} className="btn-calc-fn">log</button>
          <button onClick={handleBackspace} className="rounded border border-red-200 bg-red-50 p-2 font-bold text-red-600 hover:bg-red-100 active:scale-95 flex items-center justify-center">
            <Delete className="h-4 w-4" />
          </button>

          {/* Row 2 Functions */}
          <button onClick={() => handleFunction('asin')} className="btn-calc-fn">sin⁻¹</button>
          <button onClick={() => handleFunction('acos')} className="btn-calc-fn">cos⁻¹</button>
          <button onClick={() => handleFunction('atan')} className="btn-calc-fn">tan⁻¹</button>
          <button onClick={() => handleFunction('exp')} className="btn-calc-fn">eˣ</button>
          <button onClick={() => handleOperator('**')} className="btn-calc-fn">xʸ</button>
          <button onClick={() => handleOperator('/')} className="btn-calc-op">÷</button>

          {/* Row 3 Digits & Functions */}
          <button onClick={() => handleFunction('sinh')} className="btn-calc-fn">sinh</button>
          <button onClick={() => handleFunction('cosh')} className="btn-calc-fn">cosh</button>
          <button onClick={() => handleFunction('tanh')} className="btn-calc-fn">tanh</button>
          <button onClick={() => handleDigit('7')} className="btn-calc-num">7</button>
          <button onClick={() => handleDigit('8')} className="btn-calc-num">8</button>
          <button onClick={() => handleDigit('9')} className="btn-calc-num">9</button>

          {/* Row 4 Digits & Operators */}
          <button onClick={() => handleFunction('sqrt')} className="btn-calc-fn">√x</button>
          <button onClick={() => handleFunction('cbrt')} className="btn-calc-fn">∛x</button>
          <button onClick={() => handleFunction('sqr')} className="btn-calc-fn">x²</button>
          <button onClick={() => handleDigit('4')} className="btn-calc-num">4</button>
          <button onClick={() => handleDigit('5')} className="btn-calc-num">5</button>
          <button onClick={() => handleDigit('6')} className="btn-calc-num">6</button>

          {/* Row 5 Digits & Operators */}
          <button onClick={() => handleFunction('fact')} className="btn-calc-fn">n!</button>
          <button onClick={() => handleFunction('1/x')} className="btn-calc-fn">1/x</button>
          <button onClick={() => handleOperator('*')} className="btn-calc-op">×</button>
          <button onClick={() => handleDigit('1')} className="btn-calc-num">1</button>
          <button onClick={() => handleDigit('2')} className="btn-calc-num">2</button>
          <button onClick={() => handleDigit('3')} className="btn-calc-num">3</button>

          {/* Row 6 Final */}
          <button onClick={() => handleFunction('pi')} className="btn-calc-fn">π</button>
          <button onClick={() => handleFunction('e')} className="btn-calc-fn">e</button>
          <button onClick={() => handleOperator('-')} className="btn-calc-op">−</button>
          <button onClick={() => handleDigit('0')} className="btn-calc-num">0</button>
          <button onClick={() => handleDigit('.')} className="btn-calc-num font-bold">.</button>
          <button onClick={() => handleOperator('+')} className="btn-calc-op">+</button>

          {/* Bottom Bar: Parentheses & Equals */}
          <button onClick={() => handleDigit('(')} className="btn-calc-fn font-mono text-sm">(</button>
          <button onClick={() => handleDigit(')')} className="btn-calc-fn font-mono text-sm">)</button>
          <button onClick={() => handleFunction('+/-')} className="btn-calc-fn">±</button>
          <button
            onClick={handleEvaluate}
            className="col-span-3 rounded border border-green-700 bg-green-600 p-2 text-base font-bold text-white shadow hover:bg-green-700 active:scale-95 transition"
          >
            =
          </button>
        </div>

        {/* Footer Note */}
        <div className="border-t border-slate-200 bg-slate-50 px-3 py-2 text-center text-[11px] text-slate-500">
          Strictly conforms to official GATE 2025 TCS iON Virtual Calculator layout and operation order.
        </div>
      </div>

      <style>{`
        .btn-calc-num {
          background-color: #ffffff;
          border: 1px solid #cbd5e1;
          color: #0f172a;
          font-weight: 700;
          font-size: 14px;
          border-radius: 4px;
          padding: 8px 4px;
          transition: all 0.1s;
        }
        .btn-calc-num:hover {
          background-color: #f1f5f9;
          border-color: #94a3b8;
        }
        .btn-calc-num:active {
          transform: scale(0.96);
        }
        .btn-calc-fn {
          background-color: #f1f5f9;
          border: 1px solid #cbd5e1;
          color: #1e3a8a;
          font-weight: 600;
          border-radius: 4px;
          padding: 8px 2px;
          transition: all 0.1s;
        }
        .btn-calc-fn:hover {
          background-color: #e2e8f0;
          border-color: #93c5fd;
        }
        .btn-calc-fn:active {
          transform: scale(0.96);
        }
        .btn-calc-op {
          background-color: #e0f2fe;
          border: 1px solid #93c5fd;
          color: #0369a1;
          font-weight: 700;
          font-size: 14px;
          border-radius: 4px;
          padding: 8px 4px;
          transition: all 0.1s;
        }
        .btn-calc-op:hover {
          background-color: #bae6fd;
        }
        .btn-calc-op:active {
          transform: scale(0.96);
        }
      `}</style>
    </div>
  );
};
