#!/usr/bin/env node
/**
 * Recursively scans TypeScript and JavaScript source files and records which
 * fields are referenced. Results are written to `/tmp/frontend_usage.csv` with
 * `path,field` columns.
 *
 * Usage:
 *   tsc scripts/scan_frontend_usage.ts --outDir /tmp && \
 *   node /tmp/scripts/scan_frontend_usage.js [paths...]
 */
var __awaiter =
  (this && this.__awaiter) ||
  function (thisArg, _arguments, P, generator) {
    function adopt(value) {
      return value instanceof P
        ? value
        : new P(function (resolve) {
            resolve(value);
          });
    }
    return new (P || (P = Promise))(function (resolve, reject) {
      function fulfilled(value) {
        try {
          step(generator.next(value));
        } catch (e) {
          reject(e);
        }
      }
      function rejected(value) {
        try {
          step(generator["throw"](value));
        } catch (e) {
          reject(e);
        }
      }
      function step(result) {
        result.done
          ? resolve(result.value)
          : adopt(result.value).then(fulfilled, rejected);
      }
      step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
  };
var __generator =
  (this && this.__generator) ||
  function (thisArg, body) {
    var _ = {
        label: 0,
        sent: function () {
          if (t[0] & 1) throw t[1];
          return t[1];
        },
        trys: [],
        ops: [],
      },
      f,
      y,
      t,
      g = Object.create(
        (typeof Iterator === "function" ? Iterator : Object).prototype,
      );
    return (
      (g.next = verb(0)),
      (g["throw"] = verb(1)),
      (g["return"] = verb(2)),
      typeof Symbol === "function" &&
        (g[Symbol.iterator] = function () {
          return this;
        }),
      g
    );
    function verb(n) {
      return function (v) {
        return step([n, v]);
      };
    }
    function step(op) {
      if (f) throw new TypeError("Generator is already executing.");
      while ((g && ((g = 0), op[0] && (_ = 0)), _))
        try {
          if (
            ((f = 1),
            y &&
              (t =
                op[0] & 2
                  ? y["return"]
                  : op[0]
                    ? y["throw"] || ((t = y["return"]) && t.call(y), 0)
                    : y.next) &&
              !(t = t.call(y, op[1])).done)
          )
            return t;
          if (((y = 0), t)) op = [op[0] & 2, t.value];
          switch (op[0]) {
            case 0:
            case 1:
              t = op;
              break;
            case 4:
              _.label++;
              return { value: op[1], done: false };
            case 5:
              _.label++;
              y = op[1];
              op = [0];
              continue;
            case 7:
              op = _.ops.pop();
              _.trys.pop();
              continue;
            default:
              if (
                !((t = _.trys), (t = t.length > 0 && t[t.length - 1])) &&
                (op[0] === 6 || op[0] === 2)
              ) {
                _ = 0;
                continue;
              }
              if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) {
                _.label = op[1];
                break;
              }
              if (op[0] === 6 && _.label < t[1]) {
                _.label = t[1];
                t = op;
                break;
              }
              if (t && _.label < t[2]) {
                _.label = t[2];
                _.ops.push(op);
                break;
              }
              if (t[2]) _.ops.pop();
              _.trys.pop();
              continue;
          }
          op = body.call(thisArg, _);
        } catch (e) {
          op = [6, e];
          y = 0;
        } finally {
          f = t = 0;
        }
      if (op[0] & 5) throw op[1];
      return { value: op[0] ? op[1] : void 0, done: true };
    }
  };
var __spreadArray =
  (this && this.__spreadArray) ||
  function (to, from, pack) {
    if (pack || arguments.length === 2)
      for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
          if (!ar) ar = Array.prototype.slice.call(from, 0, i);
          ar[i] = from[i];
        }
      }
    return to.concat(ar || Array.prototype.slice.call(from));
  };
var fs = require("fs");
var path = require("path");
var roots = process.argv.slice(2);
if (roots.length === 0) {
  roots.push("apps", "packages");
}
var seen = new Set();
function scanFile(filePath) {
  return __awaiter(this, void 0, void 0, function () {
    var content, regexes, _i, regexes_1, re, match, key;
    return __generator(this, function (_a) {
      switch (_a.label) {
        case 0:
          return [4 /*yield*/, fs.promises.readFile(filePath, "utf8")];
        case 1:
          content = _a.sent();
          regexes = [
            /\.([A-Za-z_][A-Za-z0-9_]*)/g, // dot access e.g. obj.field
            /\[['"]([A-Za-z_][A-Za-z0-9_]*)['"]\]/g, // bracket access e.g. obj['field']
          ];
          for (_i = 0, regexes_1 = regexes; _i < regexes_1.length; _i++) {
            re = regexes_1[_i];
            match = void 0;
            while ((match = re.exec(content)) !== null) {
              key = "".concat(filePath, ",").concat(match[1]);
              seen.add(key);
            }
          }
          return [2 /*return*/];
      }
    });
  });
}
function walk(dir) {
  return __awaiter(this, void 0, void 0, function () {
    var entries, _i, entries_1, entry, fullPath;
    return __generator(this, function (_a) {
      switch (_a.label) {
        case 0:
          return [
            4 /*yield*/,
            fs.promises.readdir(dir, { withFileTypes: true }),
          ];
        case 1:
          entries = _a.sent();
          ((_i = 0), (entries_1 = entries));
          _a.label = 2;
        case 2:
          if (!(_i < entries_1.length)) return [3 /*break*/, 7];
          entry = entries_1[_i];
          fullPath = path.join(dir, entry.name);
          if (!entry.isDirectory()) return [3 /*break*/, 4];
          if (entry.name === "node_modules" || entry.name.startsWith("."))
            return [3 /*break*/, 6];
          return [4 /*yield*/, walk(fullPath)];
        case 3:
          _a.sent();
          return [3 /*break*/, 6];
        case 4:
          if (!/\.(ts|tsx|js|jsx)$/.test(entry.name)) return [3 /*break*/, 6];
          return [4 /*yield*/, scanFile(fullPath)];
        case 5:
          _a.sent();
          _a.label = 6;
        case 6:
          _i++;
          return [3 /*break*/, 2];
        case 7:
          return [2 /*return*/];
      }
    });
  });
}
function main() {
  return __awaiter(this, void 0, void 0, function () {
    var _i, roots_1, dir, lines;
    return __generator(this, function (_a) {
      switch (_a.label) {
        case 0:
          ((_i = 0), (roots_1 = roots));
          _a.label = 1;
        case 1:
          if (!(_i < roots_1.length)) return [3 /*break*/, 4];
          dir = roots_1[_i];
          if (!fs.existsSync(dir)) return [3 /*break*/, 3];
          return [4 /*yield*/, walk(dir)];
        case 2:
          _a.sent();
          _a.label = 3;
        case 3:
          _i++;
          return [3 /*break*/, 1];
        case 4:
          lines = __spreadArray(["path,field"], Array.from(seen), true);
          return [
            4 /*yield*/,
            fs.promises.writeFile(
              "/tmp/frontend_usage.csv",
              lines.join("\n") + "\n",
            ),
          ];
        case 5:
          _a.sent();
          return [2 /*return*/];
      }
    });
  });
}
main().catch(function (err) {
  console.error(err);
  process.exit(1);
});
