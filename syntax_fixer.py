import re
import math
LUA_KEYWORDS = {"and", "break", "do", "else", "elseif", "end", "false", "for", "function", "goto", "if", "in", "local", "nil", "not", "or", "repeat", "return", "then", "true", "until", "while", "game", "workspace", "script", "math", "string", "table", "task", "Instance", "tostring", "tonumber", "type", "error", "print", "warn", "pairs", "ipairs", "next", "pcall", "xpcall"}
def is_obfuscated(lua_code: str) -> bool:
    stripped_code = re.sub(r'--\[\[.*?\]\]', '', lua_code, flags=re.DOTALL)
    stripped_code = re.sub(r'--.*', '', stripped_code)
    clean_text = re.sub(r'\s+', '', stripped_code)
    if not clean_text:
        return False
    if re.search(r'\{\s*\d+(\s*,\s*\d+){35,}\s*\}', stripped_code):
        return True
    escaped_bytes = len(re.findall(r'\\[0-9]{3}', clean_text))
    hex_bytes = len(re.findall(r'\\x[0-9a-fA-F]{2}', clean_text))
    if escaped_bytes > 25 or hex_bytes > 25:
        return True
    vm_loop_patterns = [r'while.*do.*local.*=.*end', r'repeat.*until.*==', r'function\(.*,.*,.*,.*,.*,.*\)']
    for pattern in vm_loop_patterns:
        if len(re.findall(pattern, stripped_code)) >= 1 and len(clean_text) > 2000:
            return True
    char_calls = len(re.findall(r'string\.char', clean_text))
    sub_calls = len(re.findall(r'string\.sub', clean_text))
    if char_calls > 12 or (char_calls + sub_calls > 20):
        return True
    entropy = 0.0
    frequencies = {}
    for char in clean_text:
        frequencies[char] = frequencies.get(char, 0) + 1
    for count in frequencies.values():
        p = count / len(clean_text)
        entropy -= p * math.log2(p)
    if entropy > 6.4 and len(clean_text) > 800:
        return True
    return False
def ultimate_syntax_scanner(raw_code: str) -> str:
    fixed = re.sub(r'/\*\*(.*?)\*/', r'--[[\1]]', raw_code, flags=re.DOTALL)
    fixed = re.sub(r'//(.*)', r'--\1', fixed)
    masks = {}
    mask_idx = 0
    def mask_replacer(match):
        nonlocal mask_idx
        key = f"__MASK_{mask_idx}__"
        masks[key] = match.group(0)
        mask_idx += 1
        return key
    fixed = re.sub(r'--\[\[.*?\]\]', mask_replacer, fixed, flags=re.DOTALL)
    fixed = re.sub(r'\[\[.*?\]\]', mask_replacer, fixed, flags=re.DOTALL)
    fixed = re.sub(r'(["\'])(?:(?=(\\?))\2.)*?\1', mask_replacer, fixed)
    fixed = re.sub(r'--.*', mask_replacer, fixed)
    fixed = re.sub(r'([\)\'\"\]\}])([a-zA-Z_])', r'\1\n\2', fixed)
    fixed = re.sub(r'\b(end|then|do|else|elseif)\b([a-zA-Z_])', r'\1\n\2', fixed)
    lines = fixed.splitlines()
    clean_lines = []
    for line in lines:
        line = re.sub(r'\bfunction\s+([a-zA-Z0-9_:]+)\s*\(([^{]*?)\)\s*\{', r'function \1(\2)', line)
        line = re.sub(r'\bfunction\s*\(([^{]*?)\)\s*\{', r'function(\1)', line)
        if any(kw in line for kw in ['if ', 'if\t', 'if(']):
            line = re.sub(r'\bif\s+([^{]+)\s*\{', r'if \1 then', line)
        if any(kw in line for kw in ['elseif ', 'elseif\t']):
            line = re.sub(r'\belseif\s+([^{]+)\s*\{', r'elseif \1 then', line)
        if any(kw in line for kw in ['while ', 'while\t']):
            line = re.sub(r'\bwhile\s+([^{]+)\s*\{', r'while \1 do', line)
        if any(kw in line for kw in ['for ', 'for\t']):
            line = re.sub(r'\bfor\s+([^{]+)\s*\{', r'for \1 do', line)
        if line.strip() == "}":
            continue
        clean_lines.append(line)
    fixed = "\n".join(clean_lines)
    fixed = fixed.replace("!=", "~=")
    fixed = fixed.replace("&&", " and ")
    fixed = fixed.replace("||", " or ")
    fixed = re.sub(r'\bnull\b', 'nil', fixed, flags=re.IGNORECASE)
    fixed = re.sub(r'\blocal\s+([a-zA-Z0-9_, ]+)\s*==\s*', r'local \1 = ', fixed)
    fixed = re.sub(r'\b(if|elseif)\s+([^then\n]+?)(?<![~<>=-])=(?![=])([^then\n]+?)\bthen\b', r'\1 \2 == \3 then', fixed)
    fixed = re.sub(r'\bfunction\s+([a-zA-Z0-9_]+)\[(.*?)\]\s*\((.*?)\)', r'\1[\2] = function(\3)', fixed)
    fixed = re.sub(r'\blocal\s+([a-zA-Z0-9_]+)\s*=\s*function\s+\1\s*\(', r'local \1 = function(', fixed)
    fixed = re.sub(r'\blocal\s+function\s+([a-zA-Z0-9_]+)\s*:', r'function \1:', fixed)
    fixed = re.sub(r'\bfunction\s*\((.*?)\.\.\.\s*,\s*([^)]+)\)', r'function(\1\2, ...)', fixed)
    fixed = re.sub(r'\belse\s+elseif\b', 'elseif', fixed)
    fixed = re.sub(r'\bwhile\s+(.+?)\s+then\s+', r'while \1 do ', fixed)
    fixed = re.sub(r'\bif\s+(.+?)\s+do\s+', r'if \1 then ', fixed)
    fixed = re.sub(r'\blocal\s+(and|break|do|else|elseif|end|false|for|function|goto|if|in|local|nil|not|or|repeat|return|then|true|until|while)\b\s*=', r'local \1_var =', fixed)
    fixed = re.sub(r'\b0y([0-9a-fA-F]+)\b', r'0x\1', fixed)
    fixed = re.sub(r'\b(\d+)e\b', r'\1e0', fixed)
    fixed = re.sub(r'\bif\s+then\b', 'if true then', fixed)
    fixed = re.sub(r'\.(?=\s*[\),\n\]\}])', '', fixed)
    for key, val in reversed(masks.items()):
        fixed = fixed.replace(key, val)
    expr_lines = fixed.splitlines()
    while expr_lines:
        last_line = expr_lines[-1].strip()
        if last_line in ('end', 'end)', 'end,', '}', '})', ')'):
            expr_lines.pop()
        elif not last_line:
            expr_lines.pop()
        else:
            break
    fixed = "\n".join(expr_lines)
    token_pattern = re.compile(
        r'\b(?P<keyword>then|do|function|repeat|end|until)\b|'
        r'(?P<symbol>[\(\)\[\]\{\}])'
    )
    scope_stack = []
    clean_code_for_stack = re.sub(r'--\[\[.*?\]\]', '', fixed, flags=re.DOTALL)
    clean_code_for_stack = re.sub(r'--.*', '', clean_code_for_stack)
    clean_code_for_stack = re.sub(r'(["\'])(?:(?=(\\?))\2.)*?\1', '""', clean_code_for_stack)
    for match in token_pattern.finditer(clean_code_for_stack):
        kw = match.group('keyword')
        sym = match.group('symbol')
        if kw:
            if kw in ('then', 'do', 'function', 'repeat'):
                scope_stack.append(kw)
            elif kw == 'end':
                for i in reversed(range(len(scope_stack))):
                    if scope_stack[i] in ('then', 'do', 'function'):
                        scope_stack.pop(i)
                        break
            elif kw == 'until':
                for i in reversed(range(len(scope_stack))):
                    if scope_stack[i] == 'repeat':
                        scope_stack.pop(i)
                        break
        elif sym:
            if sym in ('(', '[', '{'):
                scope_stack.append(sym)
            elif sym == ')':
                for i in reversed(range(len(scope_stack))):
                    if scope_stack[i] == '(':
                        scope_stack.pop(i)
                        break
            elif sym == ']':
                for i in reversed(range(len(scope_stack))):
                    if scope_stack[i] == '[':
                        scope_stack.pop(i)
                        break
            elif sym == '}':
                for i in reversed(range(len(scope_stack))):
                    if scope_stack[i] == '{':
                        scope_stack.pop(i)
                        break
    appends = []
    idx = len(scope_stack) - 1
    while idx >= 0:
        token = scope_stack[idx]
        if token in ('then', 'do', 'function'):
            if token == 'function' and idx > 0 and scope_stack[idx - 1] == '(':
                appends.append("end)")
                idx -= 2
            else:
                appends.append("end")
                idx -= 1
        elif token == 'repeat':
            appends.append("until true")
            idx -= 1
        elif token == '(':
            appends.append(")")
            idx -= 1
        elif token == '{':
            appends.append("}")
            idx -= 1
        elif token == '[':
            appends.append("]")
            idx -= 1
        else:
            idx -= 1
    if appends:
        fixed += "\n" + "\n".join(appends)
    return fixed
def advanced_lua_processor(lua_code: str) -> str:
    prepared_code = ultimate_syntax_scanner(lua_code)
    dynamic_rename_map = {}
    service_pattern = r'local\s+([a-zA-Z0-9_]+)\s*=\s*game\s*:\s*(?:GetService|service)\s*\(\s*["\']([^"\']+)["\']\s*\)'
    for var_name, service_name in re.findall(service_pattern, prepared_code):
        if var_name not in LUA_KEYWORDS:
            dynamic_rename_map[var_name] = service_name
    instance_pattern = r'local\s+([a-zA-Z0-9_]+)\s*=\s*Instance\s*\.\s*new\s*\(\s*["\']([^"\']+)["\']\s*\)'
    for var_name, class_name in re.findall(instance_pattern, prepared_code):
        if var_name not in LUA_KEYWORDS:
            dynamic_rename_map[var_name] = f"Test_{class_name}"
    general_pattern = r'\b(v_[a-zA-Z0-9_]+|Nova\d+|AnalyzedVar_\d+|AnalyzedVar_\d+[a-zA-Z0-9_]+)\b'
    unique_vars = list(set(re.findall(general_pattern, prepared_code)))
    generic_counter = 1
    for var in unique_vars:
        if var not in LUA_KEYWORDS and var not in dynamic_rename_map:
            dynamic_rename_map[var] = f"AnalyzedVar_{generic_counter}"
            generic_counter += 1
    processed_text = prepared_code
    for old_name, new_name in dynamic_rename_map.items():
        processed_text = re.sub(rf'\b{old_name}\b', new_name, processed_text)
    cleaned_lines = [line.strip() for line in processed_text.splitlines() if line.strip()]
    beautified_lines = []
    indent_level = 0
    indent_string = "    "
    increase_keywords = re.compile(r'\b(do|then|repeat|function)\b|\{')
    decrease_keywords = re.compile(r'\b(end|until)\b|\}')
    for line in cleaned_lines:
        if re.match(r'^(end|until|else|elseif|\})', line):
            indent_level = max(0, indent_level - 1)
        beautified_lines.append((indent_string * indent_level) + line)
        opens = len(increase_keywords.findall(line))
        closes = len(decrease_keywords.findall(line))
        indent_level += (opens - closes)
        if re.match(r'^(else|elseif)\b', line):
            indent_level += 1
        indent_level = max(0, indent_level)
    header = "-- Steps: Renamer -> Beautify -> Full Syntax Fixed\n"
    return header + "\n".join(beautified_lines)