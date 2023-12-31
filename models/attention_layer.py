import torch
import torch.nn as nn
import torch.nn.functional as F

class Attention(nn.Module):
    def __init__(self, encoder_dim, att_type):
        super(Attention, self).__init__()
        if att_type=='additive':
            self.attention_layer = AdditiveAttention(encoder_dim)
        elif att_type=='sdotprod':
            self.attention_layer = ScaleDotProdAttention(encoder_dim)
        else:
            raise ValueError('Attention mechanism not defined: '+str(att_type))

    def forward(self, encoder_output, hidden_state, sum_context=False):
        context, alpha = self.attention_layer(encoder_output, hidden_state)
        if sum_context:
            context = context.sum(1)
        return context, alpha

# Additive Attention
class AdditiveAttention(nn.Module):
    def __init__(self, encoder_dim):
        super(AdditiveAttention, self).__init__()
        self.U = nn.Linear(512, 512)
        self.W = nn.Linear(encoder_dim, 512)
        self.v = nn.Linear(512, 1)
        self.tanh = nn.Tanh()
        self.softmax = nn.Softmax(1)

    def forward(self, encoder_output, hidden_state):
        # encoder_output ------ torch.Size([24, 49, 2048])
        # hidden_state ------ torch.Size([24, 512])
        U_h = self.U(hidden_state).unsqueeze(1)
        # Uh ------ torch.Size([24, 1, 512])
        W_s = self.W(encoder_output)
        # Ws (s=encoder_output) ------ torch.Size([24, 49, 512])
        att = self.tanh(W_s + U_h)
        # a = tanh(Ws + Uh) ------ torch.Size([24, 49, 512])
        e = self.v(att).squeeze(2)
        # e = V^tanh(Ws + Uh) ------ torch.Size([24, 49])
        alpha = self.softmax(e)
        # alpha ------ torch.Size([24, 49])
        context = (encoder_output * alpha.unsqueeze(2))
        # context ------ torch.Size([24, 49, 2048])
        return context, alpha


# Scaled Dot-Product
class ScaleDotProdAttention(nn.Module):
    def __init__(self, encoder_dim, att_size=512):
        super(ScaleDotProdAttention, self).__init__()
        # raise NotImplementedError("TODO: Implement attention layer")
        # Matrices can be seen as linear layers without bias
        self.W_Q = nn.Linear(encoder_dim, att_size)
        self.W_K = nn.Linear(encoder_dim, att_size)
        self.W_V = nn.Linear(encoder_dim, encoder_dim)
        self.encoder_dim = encoder_dim
        self.softmax = nn.Softmax(1)
        self.scale_score = 1. / float(att_size)** 0.5

    def forward(self, encoder_output, cls_vector):
        # encoder_output ------ torch.Size([Bs, hxw, encoder_dim])
        # cls_vector ------ torch.Size([1, 512])

        # raise NotImplementedError("TODO: Calculate query, key and vector")
        query = self.W_Q(cls_vector)
        key = self.W_K(encoder_output)
        value = self.W_V(encoder_output)

        # query ------ torch.Size([1, att_size])
        # key ------ torch.Size([Bs, hxw, att_size])
        # value ------ torch.Size([Bs, hxw, encoder_dim])
        
        # raise NotImplementedError("TODO: Calculate the dot product, \
        #     multiply by the scale factor, apply softmax to get the attention")
        att = torch.matmul(query.unsqueeze(1), torch.transpose(key, 1, 2))
        att_scaled = att / torch.sqrt(self.encoder_dim)
        # att (mixed dot product) ------ torch.Size([Bs, hxw])

        alpha = self.softmax(att_scaled)
        # alpha ------ torch.Size([24, 49])
        context = (value * alpha.unsqueeze(2))
        # context ------ torch.Size([24, 49, 2048])
        return context, alpha

if __name__ == "__main__":
    model = Attention(512, 'additive').cuda()
    model.eval()
    print(model)
    encoder_output = torch.randn(2, 256, 512).cuda()
    v_embedding = torch.randn(2, 512).cuda()
    with torch.no_grad():
        output, alpha = model.forward(encoder_output, v_embedding)
    print(output.size())
    print(alpha.size())
