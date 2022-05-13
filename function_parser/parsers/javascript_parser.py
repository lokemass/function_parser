import time
from typing import List, Dict, Any

from function_parser.parsers.language_parser import LanguageParser, match_from_span, tokenize_code, traverse_type, \
    previous_sibling, \
    node_parent
from function_parser.parsers.commentutils import get_docstring_summary, strip_c_style_comment_delimiters


class JavascriptParser(LanguageParser):
    FILTER_PATHS = ('test', 'node_modules')

    BLACKLISTED_FUNCTION_NAMES = {'toString', 'toLocaleString', 'valueOf'}

    @staticmethod
    def get_docstring(tree, node, blob: str) -> str:
        doc_time = time.time()
        docstring = ''
        parent_node = node_parent(tree, node)

        if parent_node.type == 'variable_declarator':
            base_node = node_parent(tree, parent_node)  # Get the variable declaration
        elif parent_node.type == 'pair':
            base_node = parent_node  # This is a common pattern where a function is assigned as a value to a dictionary.
        else:
            base_node = node
        previous_sibling_time = time.time()
        prev_sibling = previous_sibling(tree, base_node)
        if prev_sibling is not None and prev_sibling.type == 'comment':
            all_prev_comment_nodes = [prev_sibling]
            prev_sibling = previous_sibling(tree, prev_sibling)
            while prev_sibling is not None and prev_sibling.type == 'comment':
                all_prev_comment_nodes.append(prev_sibling)
                last_comment_start_line = prev_sibling.start_point[0]
                prev_sibling = previous_sibling(tree, prev_sibling)
                if prev_sibling is None:
                    break
                if prev_sibling.end_point[0] + 1 < last_comment_start_line:
                    break  # if there is an empty line, stop expanding.
            # print("previous sibling processing time", time.time()-previous_sibling_time)
            docstring = ' '.join(
                (strip_c_style_comment_delimiters(match_from_span(s, blob)) for s in all_prev_comment_nodes[::-1]))

        # print("get docstring time ->", time.time() - doc_time)
        return docstring

    # @staticmethod
    # def get_definition(tree, blob: str) -> List[Dict[str, Any]]:
    #     function_nodes = []
    #     functions = []
    #     start = time.time()
    #     traverse_type(tree.root_node, function_nodes, 'function')
    #     print("get_definition.traverse_type", time.time() - start)
    #     # print("for loop started function", time.time()-start)
    #     get_definition_function_loop = time.time()
    #     for function in function_nodes:
    #         if function.children is None or len(function.children) == 0:
    #             continue
    #         else:
    #             parent_node_time = time.time()
    #             parent_node = node_parent(tree, function)
    #             print("parent node processing time", time.time() - parent_node_time)
    #             functions.append((parent_node.type, function, JavascriptParser.get_docstring(tree, function, blob)))
    #     #     print("for loop function iteration = ", time.time() - start)
    #     print("get_definition_function_loop processing time= ", time.time() - get_definition_function_loop)
    #     definitions = []
    #     meta_start = time.time()
    #     for node_type, function_node, docstring in functions:
    #
    #         metadata = JavascriptParser.get_function_metadata(function_node, blob)
    #         docstring_summary = get_docstring_summary(docstring)
    #
    #         if metadata['identifier'] in JavascriptParser.BLACKLISTED_FUNCTION_NAMES:
    #             continue
    #         definitions.append({
    #             'type': node_type,
    #             'identifier': metadata['identifier'],
    #             'parameters': metadata['parameters'],
    #             'function': match_from_span(function_node, blob),
    #             'function_tokens': tokenize_code(function_node, blob),
    #             'docstring': docstring,
    #             'docstring_summary': docstring_summary,
    #             'start_point': function_node.start_point,
    #             'end_point': function_node.end_point
    #         })
    #     print("metadata processing time -> ", time.time() - meta_start)
    #     return definitions

    @staticmethod
    def get_definition(tree, blob: str) -> List[Dict[str, Any]]:
        function_nodes = []
        definitions = []
        # functions = []
        start = time.time()
        traverse_type(tree.root_node, function_nodes, 'function')
        print("get_definition.traverse_type", time.time() - start)
        # print("for loop started function", time.time()-start)
        get_definition_function_loop = time.time()
        for function in function_nodes:
            if function.children is None or len(function.children) == 0:
                continue
            else:
                parent_node = node_parent(tree, function)
                node_type, function_node, docstring = parent_node.type, function, JavascriptParser.get_docstring(tree,
                                                                                                                 function,
                                                                                                                 blob)
                metadata = JavascriptParser.get_function_metadata(function_node, blob)
                docstring_summary = get_docstring_summary(docstring)

                if metadata['identifier'] not in JavascriptParser.BLACKLISTED_FUNCTION_NAMES:
                    # continue
                    definitions.append({
                        'type': node_type,
                        'identifier': metadata['identifier'],
                        'parameters': metadata['parameters'],
                        'function': match_from_span(function_node, blob),
                        'function_tokens': tokenize_code(function_node, blob),
                        'docstring': docstring,
                        'docstring_summary': docstring_summary,
                        'start_point': function_node.start_point,
                        'end_point': function_node.end_point
                    })
                print("Function name =", metadata['identifier'])
        return definitions

    @staticmethod
    def get_function_metadata(function_node, blob: str) -> Dict[str, str]:
        meta_time = time.time()
        metadata = {
            'identifier': '',
            'parameters': '',
        }
        identifier_nodes = [child for child in function_node.children if child.type == 'identifier']
        formal_parameters_nodes = [child for child in function_node.children if child.type == 'formal_parameters']
        if identifier_nodes:
            metadata['identifier'] = match_from_span(identifier_nodes[0], blob)
        if formal_parameters_nodes:
            metadata['parameters'] = match_from_span(formal_parameters_nodes[0], blob)
        print("get_function_metadata processing time", time.time() - meta_time)
        return metadata
