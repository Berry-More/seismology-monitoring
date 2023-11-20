b_value_js = """
        const inds = cb_obj.indices;
        const d1 = s1.data;
        const d2 = s2.data;

        d2['x'] = [];
        d2['y'] = [];

        let n = inds.length;

        let sumxy = 0;
        let sumx = 0;
        let sumy = 0;
        let sumx2 = 0;
        
        for (let i = 0; i < n; i++)
        {
            sumx += d1['x'][inds[i]];
            sumy += d1['y'][inds[i]];
            sumx2 += d1['x'][inds[i]] **2;
            sumxy += d1['x'][inds[i]] * d1['y'][inds[i]];
            
            d2['x'].push(d1['x'][inds[i]]);
        }
            
        let a = (n * sumxy - sumx * sumy) / (n * sumx2 - sumx ** 2)
        let b = (sumy - a * sumx) / n
        
        for (let i = 0; i < n; i++)
        {            
            d2['y'].push(a * d1['x'][inds[i]] + b);
        }
        
        a = a * -1
        const line = 'a-value = ' + b.toFixed(2) + ', b-value = ' + a.toFixed(2);
        div.text = line;
        
        s2.change.emit();
        """


profile_js = """
        const inds = cb_obj.indices;
        const d1 = s1.data;
        
        for (let i = 0; i < inds.length; i++)
        {
            alert(inds[i]);
        }
"""
