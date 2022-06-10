import mistletoe

import environment_or_equation_reference_parser
import include_parser
import latex_parser
import page_link_parser

class nLabSourceRenderer(mistletoe.html_renderer.HTMLRenderer):
    def __init__(self):
        super().__init__(
            latex_parser.InlineLatexToken,
            latex_parser.StandAloneLatexToken,
            page_link_parser.SimplePageLinkToken,
            page_link_parser.PageLinkWithDisplayTextToken,
            environment_or_equation_reference_parser.EnvironmentOrEquationReferenceToken,
            environment_or_equation_reference_parser.EquationReferenceToken,
            include_parser.IncludeToken)

    def _render_latex_token(self, token):
        try:
            return token.render()
        except latex_parser.LatexTokenRendererException as exception:
            # TODO. Also handle subprocess exception. Maybe in render() function: need to handle general exception
            raise exception

    def render_inline_latex_token(self, token):
        return self._render_latex_token(token)

    def render_stand_alone_latex_token(self, token):
        return self._render_latex_token(token)

    def render_simple_page_link_token(self, token):
        return token.render()

    def render_page_link_with_display_text_token(self, token):
        return token.render()

    def render_environment_or_equation_reference_token(self, token):
        return token.render()

    def render_equation_reference_token(self, token):
        return token.render()

    def render_include_token(self, token):
        return token.render()

def render(source):
    with nLabSourceRenderer() as renderer:
        rendered_source = renderer.render(mistletoe.Document(source))
    return rendered_source
